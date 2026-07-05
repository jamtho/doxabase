"""Query target and storage-route candidate discovery and ranking.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via QueryCandidatesMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class QueryCandidatesMixin:
    def _query_context_database_relation_candidates_from_evidence(
        self,
        dataset: DatasetDescription,
        *,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        evidence_iris = self._query_context_dataset_query_evidence_iris(
            dataset.iri,
            exclude_evidence_iris=set(),
        )
        candidates: list[dict[str, Any]] = []
        seen_candidates: set[tuple[str, str]] = set()
        total_count = 0
        for evidence_iri in evidence_iris:
            evidence = self._describe_evidence(
                evidence_iri,
                self._expand_graphs(["evidence"]),
                self._lookup_graphs(self._expand_graphs(["all"])),
            )
            for handle in evidence.scanned_source_handles:
                parsed = self._query_database_relation_candidate_from_handle(handle)
                if parsed is None:
                    continue
                connection_reference, relation_identifier = parsed
                candidate_key = (connection_reference, relation_identifier)
                if candidate_key in seen_candidates:
                    continue
                seen_candidates.add(candidate_key)
                total_count += 1
                if len(candidates) >= limit:
                    continue
                candidate_arguments = {
                    "storage_protocol": "rc:DatabaseStorage",
                    "storage_root": connection_reference,
                    "location_kind": "connection",
                    "path_templates": [relation_identifier],
                }
                candidates.append(
                    {
                        "candidate_rank": len(candidates) + 1,
                        "candidate_kind": "database_relation_from_query_evidence",
                        "requires_review": True,
                        "review_status": "review_required",
                        "evidence_iri": evidence_iri,
                        "scanned_source_handle": handle.strip(),
                        "connection_reference": connection_reference,
                        "relation_identifier": relation_identifier,
                        "storage_protocol": "rc:DatabaseStorage",
                        "storage_root": connection_reference,
                        "location_kind": "connection",
                        "path_templates": [relation_identifier],
                        "query_storage_access_repair_candidate_spec": (
                            candidate_arguments
                        ),
                        "candidate_value_fields": [
                            "storage_protocol",
                            "storage_root",
                            "location_kind",
                            "path_templates",
                        ],
                        "review_note": (
                            "Parsed from a query-result scanned_source_handle. "
                            "Copy these values into the stage_revision "
                            "query_storage_access_repair spec only after "
                            "reviewing the handle as a non-secret database "
                            "relation route."
                        ),
                    }
                )
        return candidates, total_count
    def _query_context_evidence_storage_route_candidates_from_evidence(
        self,
        dataset: DatasetDescription,
        *,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        evidence_iris = self._query_context_dataset_query_evidence_iris(
            dataset.iri,
            exclude_evidence_iris=set(),
        )
        candidates: list[dict[str, Any]] = []
        seen_candidates: set[tuple[Any, ...]] = set()
        total_count = 0
        for evidence_iri in evidence_iris:
            evidence = self._describe_evidence(
                evidence_iri,
                self._expand_graphs(["evidence"]),
                self._lookup_graphs(self._expand_graphs(["all"])),
            )
            evidence_candidates = self._evidence_storage_route_candidates_for_evidence(
                evidence,
                limit=limit,
                seen_candidates=seen_candidates,
                start_rank=len(candidates) + 1,
            )
            total_count += evidence_candidates[1]
            for candidate in evidence_candidates[0]:
                if len(candidates) >= limit:
                    break
                candidate["candidate_rank"] = len(candidates) + 1
                candidates.append(candidate)
        return candidates, total_count
    def _query_context_evidence_storage_route_candidates_for_evidence(
        self,
        evidence_iri: str,
        *,
        limit: int,
        evidence: EvidenceDescription | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        evidence_description = evidence or self._describe_evidence(
            evidence_iri,
            self._expand_graphs(["evidence"]),
            self._lookup_graphs(self._expand_graphs(["all"])),
        )
        return self._evidence_storage_route_candidates_for_evidence(
            evidence_description,
            limit=limit,
            seen_candidates=set(),
            start_rank=1,
        )
    def _evidence_storage_route_candidates_for_evidence(
        self,
        evidence: EvidenceDescription,
        *,
        limit: int,
        seen_candidates: set[tuple[Any, ...]],
        start_rank: int,
    ) -> tuple[list[dict[str, Any]], int]:
        candidates: list[dict[str, Any]] = []
        total_count = 0
        scanned_source_kind = self.expand_iri("rc:DataSampleSource")
        source_values: list[tuple[str, str]] = []
        for span in evidence.source_spans:
            if span.source_kind == scanned_source_kind and span.source_path:
                source_values.append(("scanned_source_paths", span.source_path))
        existing_values = {value for _, value in source_values}
        for handle in evidence.scanned_source_handles:
            if handle not in existing_values:
                source_values.append(("scanned_source_handles", handle))
                existing_values.add(handle)
        for source_field, source_value in source_values:
            candidate = self._evidence_storage_route_candidate_from_value(
                evidence_iri=evidence.iri,
                source_field=source_field,
                source_value=source_value,
            )
            if candidate is None:
                continue
            candidate_key = self._evidence_storage_route_candidate_key(candidate)
            if candidate_key in seen_candidates:
                continue
            seen_candidates.add(candidate_key)
            total_count += 1
            candidates.append(candidate)
        candidates = sorted(
            candidates,
            key=self._evidence_storage_route_candidate_sort_key,
        )
        candidates = candidates[:limit]
        for index, candidate in enumerate(candidates):
            candidate["candidate_rank"] = start_rank + index
        return candidates, total_count
    @staticmethod
    def _evidence_storage_route_candidate_sort_key(
        candidate: Mapping[str, Any],
    ) -> tuple[int, str, str]:
        priority = {
            "database_relation_from_query_evidence": 0,
            "s3_path_from_query_evidence": 1,
            "local_path_from_query_evidence": 2,
        }
        return (
            priority.get(str(candidate.get("candidate_kind")), 99),
            str(candidate.get("source_field") or ""),
            str(candidate.get("source_value") or ""),
        )
    @staticmethod
    def _evidence_storage_route_candidate_key(
        candidate: Mapping[str, Any],
    ) -> tuple[Any, ...]:
        return (
            candidate.get("candidate_kind"),
            candidate.get("storage_protocol"),
            candidate.get("storage_root"),
            candidate.get("location_kind"),
            tuple(candidate.get("path_templates") or []),
            candidate.get("bucket_name"),
            candidate.get("key_prefix"),
        )
    def _evidence_storage_route_candidate_from_value(
        self,
        *,
        evidence_iri: str,
        source_field: str,
        source_value: str,
    ) -> dict[str, Any] | None:
        value = source_value.strip()
        if not value:
            return None
        parsed_database = self._query_database_relation_candidate_from_handle(value)
        if parsed_database is not None and source_field == "scanned_source_handles":
            connection_reference, relation_identifier = parsed_database
            storage_arguments = {
                "storage_protocol": "rc:DatabaseStorage",
                "storage_root": connection_reference,
                "location_kind": "connection",
                "path_templates": [relation_identifier],
            }
            overlay_arguments = {
                **storage_arguments,
                "file_format": "REVIEWED_DATABASE_TABLE_FILE_FORMAT",
            }
            return self._evidence_storage_route_candidate(
                candidate_kind="database_relation_from_query_evidence",
                evidence_iri=evidence_iri,
                source_field=source_field,
                source_value=value,
                storage_arguments=storage_arguments,
                overlay_arguments=overlay_arguments,
                candidate_value_fields=[
                    "storage_protocol",
                    "storage_root",
                    "location_kind",
                    "path_templates",
                ],
                review_note=(
                    "Parsed from a query-result scanned_source_handle. Review "
                    "the handle as a non-secret database relation route before "
                    "using the candidate arguments."
                ),
                extra_fields={
                    "connection_reference": connection_reference,
                    "relation_identifier": relation_identifier,
                    "scanned_source_handle": value,
                },
            )
        s3_candidate = self._s3_storage_route_candidate_from_value(
            evidence_iri=evidence_iri,
            source_field=source_field,
            source_value=value,
        )
        if s3_candidate is not None:
            return s3_candidate
        return self._local_storage_route_candidate_from_value(
            evidence_iri=evidence_iri,
            source_field=source_field,
            source_value=value,
        )
    def _s3_storage_route_candidate_from_value(
        self,
        *,
        evidence_iri: str,
        source_field: str,
        source_value: str,
    ) -> dict[str, Any] | None:
        parsed = urlparse(source_value)
        if parsed.scheme.lower() != "s3" or not parsed.netloc:
            return None
        key = parsed.path.lstrip("/")
        if not key:
            return None
        bucket = parsed.netloc
        file_format = self._query_file_format_from_path(key)
        storage_arguments: dict[str, Any] = {
            "storage_protocol": "rc:S3CompatibleStorage",
            "storage_root": f"s3://{bucket}",
            "location_kind": "prefix",
            "bucket_name": bucket,
            "key_prefix": self._query_path_prefix_before_leaf_or_glob(key),
            "path_templates": [key],
        }
        overlay_arguments = dict(storage_arguments)
        if file_format is not None:
            overlay_arguments["file_format"] = file_format
        return self._evidence_storage_route_candidate(
            candidate_kind="s3_path_from_query_evidence",
            evidence_iri=evidence_iri,
            source_field=source_field,
            source_value=source_value,
            storage_arguments=storage_arguments,
            overlay_arguments=overlay_arguments,
            candidate_value_fields=[
                "storage_protocol",
                "storage_root",
                "location_kind",
                "bucket_name",
                "key_prefix",
                "path_templates",
                *([] if file_format is None else ["file_format"]),
            ],
            review_note=(
                "Parsed from query-result source evidence. Review the S3 path "
                "as non-secret route metadata; endpoint profiles, regions, "
                "path-style access, and credential references are not inferred "
                "from the URI."
            ),
            extra_fields={
                "bucket_name": bucket,
                "key_prefix": storage_arguments["key_prefix"],
                "path_templates": [key],
                "file_format": file_format,
            },
        )
    def _local_storage_route_candidate_from_value(
        self,
        *,
        evidence_iri: str,
        source_field: str,
        source_value: str,
    ) -> dict[str, Any] | None:
        if "://" in source_value:
            return None
        if self._query_database_relation_candidate_from_handle(source_value) is not None:
            return None
        if not self._query_value_looks_like_local_path(source_value):
            return None
        normalized = source_value.replace("\\", "/")
        directory = posixpath.dirname(normalized)
        leaf = posixpath.basename(normalized)
        if not leaf:
            return None
        if directory:
            storage_root = directory
            path_templates = [leaf]
            location_kind = "directory"
        else:
            storage_root = source_value
            path_templates = []
            location_kind = "object"
        file_format = self._query_file_format_from_path(source_value)
        storage_arguments: dict[str, Any] = {
            "storage_protocol": "rc:LocalFilesystemStorage",
            "storage_root": storage_root,
            "location_kind": location_kind,
        }
        if path_templates:
            storage_arguments["path_templates"] = path_templates
        overlay_arguments = dict(storage_arguments)
        if file_format is not None:
            overlay_arguments["file_format"] = file_format
        return self._evidence_storage_route_candidate(
            candidate_kind="local_path_from_query_evidence",
            evidence_iri=evidence_iri,
            source_field=source_field,
            source_value=source_value,
            storage_arguments=storage_arguments,
            overlay_arguments=overlay_arguments,
            candidate_value_fields=[
                "storage_protocol",
                "storage_root",
                "location_kind",
                *(["path_templates"] if path_templates else []),
                *([] if file_format is None else ["file_format"]),
            ],
            review_note=(
                "Parsed from query-result source evidence. Review the local "
                "path as collaborator-safe route metadata before using the "
                "candidate arguments."
            ),
            extra_fields={
                "path_templates": path_templates,
                "file_format": file_format,
            },
        )
    def _evidence_storage_route_candidate(
        self,
        *,
        candidate_kind: str,
        evidence_iri: str,
        source_field: str,
        source_value: str,
        storage_arguments: dict[str, Any],
        overlay_arguments: dict[str, Any],
        candidate_value_fields: list[str],
        review_note: str,
        extra_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        candidate = {
            "candidate_rank": 0,
            "candidate_kind": candidate_kind,
            "requires_review": True,
            "review_status": "review_required",
            "evidence_iri": evidence_iri,
            "source_field": source_field,
            "source_value": source_value,
            "storage_protocol": storage_arguments.get("storage_protocol"),
            "storage_root": storage_arguments.get("storage_root"),
            "location_kind": storage_arguments.get("location_kind"),
            "path_templates": storage_arguments.get("path_templates", []),
            "query_storage_access_repair_candidate_spec": (
                storage_arguments
            ),
            "query_evidence_overlay_candidate_spec": (
                overlay_arguments
            ),
            "candidate_value_fields": candidate_value_fields,
            "review_note": review_note,
        }
        if extra_fields:
            candidate.update(extra_fields)
        return candidate
    @staticmethod
    def _query_database_relation_candidate_from_handle(
        handle: str,
    ) -> tuple[str, str] | None:
        value = handle.strip()
        if not value:
            return None
        if "://" in value or "/" in value or "\\" in value:
            return None
        if value.count(":") != 1:
            return None
        connection_reference, relation_identifier = (
            part.strip() for part in value.split(":", 1)
        )
        if not connection_reference or not relation_identifier:
            return None
        if len(connection_reference) == 1 and connection_reference.isalpha():
            return None
        if not re.fullmatch(r"[A-Za-z0-9_.@$-]+", connection_reference):
            return None
        if re.search(r"\s", relation_identifier):
            return None
        if ":" in relation_identifier:
            return None
        if not re.fullmatch(r"[A-Za-z0-9_.@$-]+", relation_identifier):
            return None
        return connection_reference, relation_identifier
    def _query_context_candidate_only_layout_blocked(
        self,
        candidate: QueryTargetCandidate,
    ) -> bool:
        direct_blockers = self._query_target_blocking_reasons(
            candidate.direct_review_reasons
        )
        return bool(direct_blockers) and all(
            reason.code == "ambiguous_physical_layout"
            for reason in direct_blockers
        )
    def _query_target_candidates(
        self,
        dataset: DatasetDescription,
        *,
        dataset_summary: ResourceSummary,
        direct_path_templates: list[str],
        issues: list[QueryPlanningIssue],
    ) -> list[QueryTargetCandidate]:
        template_sources: list[tuple[str, str, ResourceSummary]] = []
        seen_sources: set[tuple[str, str, str]] = set()

        def add_template_source(
            template: str | None,
            template_source: str,
            source_resource: ResourceSummary,
        ) -> None:
            if template is None:
                return
            key = (template, template_source, source_resource.iri)
            if key in seen_sources:
                return
            seen_sources.add(key)
            template_sources.append((template, template_source, source_resource))

        for template in direct_path_templates:
            add_template_source(template, "dataset", dataset_summary)
        for partition in dataset.partition_schemes:
            add_template_source(
                partition.path_template,
                "partition_scheme",
                self._summary_from_description(partition),
            )

        candidates: list[QueryTargetCandidate] = []
        seen_candidates: set[tuple[str, str, str, str | None]] = set()

        def add_candidate(
            template: str,
            template_source: str,
            source_resource: ResourceSummary,
            storage_access: StorageAccessDescription | None,
        ) -> None:
            access_resource = (
                self._summary_from_description(storage_access)
                if storage_access is not None
                else None
            )
            key = (
                template,
                template_source,
                source_resource.iri,
                access_resource.iri if access_resource is not None else None,
            )
            if key in seen_candidates:
                return
            seen_candidates.add(key)
            database_storage = (
                storage_access is not None
                and self._is_database_storage(storage_access.storage_protocol)
            )
            template_has_applicable_non_database_candidate = (
                database_storage
                and template_source
                not in {"storage_access", "storage_access_location"}
                and self._query_template_has_applicable_non_database_candidate(
                    dataset,
                    template=template,
                    template_source=template_source,
                    source_resource=source_resource,
                )
            )
            if template_has_applicable_non_database_candidate:
                return
            database_relation_template_source_mismatch = (
                database_storage
                and template_source not in {"storage_access", "storage_access_location"}
            )
            relation_identifier = (
                template.strip() or None
                if database_storage and template_source == "storage_access"
                else None
            )
            connection_reference = (
                storage_access.storage_root
                if database_storage and storage_access is not None
                else None
            )
            if template_source == "storage_access_location":
                candidate_path = template.strip() or None
                if database_storage:
                    composition = (
                        "database_connection_as_candidate"
                        if candidate_path is not None
                        else "unresolved"
                    )
                else:
                    composition = (
                        "storage_root_as_candidate"
                        if candidate_path is not None
                        else "unresolved"
                    )
            elif database_storage:
                if database_relation_template_source_mismatch:
                    candidate_path = None
                    composition = "unresolved"
                else:
                    candidate_path = relation_identifier
                    if candidate_path is None:
                        composition = "unresolved"
                    elif connection_reference:
                        composition = "database_connection_and_relation"
                    else:
                        composition = "database_relation"
            else:
                candidate_path, composition = self._query_candidate_path(
                    template,
                    storage_access,
                )
            review_reasons = self._query_target_review_reasons(
                dataset,
                issues,
                source_resource=source_resource,
                storage_access=access_resource,
            )
            if (
                storage_access is not None
                and template_source != "storage_access_location"
            ):
                object_location_issue = (
                    self._query_storage_object_location_template_issue(
                        template=template,
                        template_source=template_source,
                        source_resource=source_resource,
                        storage_access=storage_access,
                    )
                )
                if object_location_issue is not None and not any(
                    reason.code == object_location_issue.code
                    and (
                        reason.resource.iri if reason.resource is not None else None
                    )
                    == (
                        object_location_issue.resource.iri
                        if object_location_issue.resource is not None
                        else None
                    )
                    for reason in review_reasons
                ):
                    review_reasons.append(object_location_issue)
                relation_source_issue = None
                if not self._query_template_has_applicable_non_database_candidate(
                    dataset,
                    template=template,
                    template_source=template_source,
                    source_resource=source_resource,
                ):
                    relation_source_issue = (
                        self._query_database_relation_template_source_issue(
                            template=template,
                            template_source=template_source,
                            source_resource=source_resource,
                            storage_access=storage_access,
                        )
                    )
                if relation_source_issue is not None and not any(
                    reason.code == relation_source_issue.code
                    and (
                        reason.resource.iri if reason.resource is not None else None
                    )
                    == (
                        relation_source_issue.resource.iri
                        if relation_source_issue.resource is not None
                        else None
                    )
                    for reason in review_reasons
                ):
                    review_reasons.append(relation_source_issue)
                candidate_metadata_issue = self._query_candidate_metadata_issue(
                    template=template,
                    source_resource=source_resource,
                    storage_access=storage_access,
                )
                if candidate_metadata_issue is not None and not any(
                    reason.code == candidate_metadata_issue.code
                    and (
                        reason.resource.iri if reason.resource is not None else None
                    )
                    == (
                        candidate_metadata_issue.resource.iri
                        if candidate_metadata_issue.resource is not None
                        else None
                    )
                    for reason in review_reasons
                ):
                    review_reasons.append(candidate_metadata_issue)
                format_issue = (
                    self._query_candidate_path_extension_physical_layout_issue(
                        candidate_path=candidate_path,
                        template=template,
                        template_source=template_source,
                        source_resource=source_resource,
                        physical_layouts=dataset.physical_layouts,
                    )
                )
                if format_issue is not None and not any(
                    reason.code == format_issue.code
                    and (
                        reason.resource.iri if reason.resource is not None else None
                    )
                    == (
                        format_issue.resource.iri
                        if format_issue.resource is not None
                        else None
                    )
                    for reason in review_reasons
                ):
                    review_reasons.append(format_issue)
            if (
                storage_access is not None
                and template_source == "storage_access_location"
            ):
                location_issue = self._query_storage_access_location_kind_issue(
                    storage_access
                )
                if location_issue is not None and not any(
                    reason.code == location_issue.code
                    and (
                        reason.resource.iri if reason.resource is not None else None
                    )
                    == (
                        location_issue.resource.iri
                        if location_issue.resource is not None
                        else None
                    )
                    for reason in review_reasons
                ):
                    review_reasons.append(location_issue)
                format_issue = (
                    self._query_candidate_path_extension_physical_layout_issue(
                        candidate_path=candidate_path,
                        template=template,
                        template_source=template_source,
                        source_resource=source_resource,
                        physical_layouts=dataset.physical_layouts,
                    )
                )
                if format_issue is not None and not any(
                    reason.code == format_issue.code
                    and (
                        reason.resource.iri if reason.resource is not None else None
                    )
                    == (
                        format_issue.resource.iri
                        if format_issue.resource is not None
                        else None
                    )
                    for reason in review_reasons
                ):
                    review_reasons.append(format_issue)
            review_required = any(
                reason.severity in {"error", "warning"}
                for reason in review_reasons
            )
            direct_review_reasons = self._query_target_direct_review_reasons(
                review_reasons
            )
            direct_review_required = any(
                reason.severity in {"error", "warning"}
                for reason in direct_review_reasons
            )
            candidate_selector = self._query_target_candidate_selector(
                template=template,
                template_source=template_source,
                source_resource_iri=source_resource.iri,
                storage_access_iri=(
                    access_resource.iri if access_resource is not None else None
                ),
            )
            candidates.append(
                QueryTargetCandidate(
                    candidate_selector=candidate_selector,
                    template=template,
                    template_source=template_source,
                    source_resource=source_resource,
                    storage_access=access_resource,
                    route_roles=(
                        list(storage_access.route_roles)
                        if storage_access is not None
                        else []
                    ),
                    storage_protocol=(
                        storage_access.storage_protocol
                        if storage_access is not None
                        else None
                    ),
                    access_mode=(
                        storage_access.access_mode
                        if storage_access is not None
                        else None
                    ),
                    location_kind=(
                        storage_access.location_kind
                        if storage_access is not None
                        else None
                    ),
                    storage_root=(
                        storage_access.storage_root
                        if storage_access is not None
                        else None
                    ),
                    endpoint_profile=(
                        storage_access.endpoint_profile
                        if storage_access is not None
                        else None
                    ),
                    bucket_name=(
                        storage_access.bucket_name if storage_access is not None else None
                    ),
                    key_prefix=(
                        storage_access.key_prefix if storage_access is not None else None
                    ),
                    region=(
                        storage_access.region if storage_access is not None else None
                    ),
                    candidate_path=candidate_path,
                    relation_identifier=relation_identifier,
                    connection_reference=connection_reference,
                    composition=composition,
                    candidate_path_status=self._query_candidate_path_status(
                        candidate_path,
                        review_required=review_required,
                        review_reasons=review_reasons,
                    ),
                    requires_endpoint_profile=(
                        bool(storage_access.endpoint_profile)
                        if storage_access is not None
                        else False
                    ),
                    credential_reference=(
                        storage_access.credential_reference
                        if storage_access is not None
                        else None
                    ),
                    path_style_access=(
                        storage_access.path_style_access
                        if storage_access is not None
                        else None
                    ),
                    review_required=review_required,
                    review_reasons=review_reasons,
                    direct_review_required=direct_review_required,
                    direct_review_reasons=direct_review_reasons,
                )
            )

        for template, template_source, source_resource in template_sources:
            if dataset.storage_accesses:
                for storage_access in dataset.storage_accesses:
                    add_candidate(template, template_source, source_resource, storage_access)
            else:
                add_candidate(template, template_source, source_resource, None)
        for storage_access in dataset.storage_accesses:
            access_resource = self._summary_from_description(storage_access)
            for template in storage_access.path_templates:
                add_candidate(template, "storage_access", access_resource, storage_access)
            if storage_access.storage_root is not None and (
                (
                    not template_sources
                    and not storage_access.path_templates
                )
                or (
                    storage_access.location_kind == "object"
                    and not self._is_database_storage(storage_access.storage_protocol)
                )
            ):
                add_candidate(
                    storage_access.storage_root,
                    "storage_access_location",
                    access_resource,
                    storage_access,
                )

        return [
            self._query_target_candidate_with_binding_summary(candidate, dataset)
            for candidate in candidates
        ]
    def _query_target_candidate_with_binding_summary(
        self,
        candidate: QueryTargetCandidate,
        dataset: DatasetDescription,
    ) -> QueryTargetCandidate:
        binding_requirements = self._draft_query_plan_binding_requirements(
            candidate,
            columns=dataset.columns,
            partition_schemes=dataset.partition_schemes,
        )
        binding_examples = self._query_plan_action_binding_examples(
            candidate,
            binding_requirements,
        )
        return replace(
            candidate,
            required_bindings=self._query_plan_required_binding_names(
                binding_requirements
            ),
            required_binding_details=self._query_plan_required_binding_details(
                binding_requirements
            ),
            binding_example=self._query_plan_action_binding_example_summary(
                binding_examples
            ),
            binding_examples=binding_examples,
        )
    @staticmethod
    def _query_target_candidate_selector(
        *,
        template: str,
        template_source: str,
        source_resource_iri: str,
        storage_access_iri: str | None,
    ) -> str:
        payload = {
            "template": template,
            "template_source": template_source,
            "source_resource_iri": source_resource_iri,
            "storage_access_iri": storage_access_iri,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
        return f"query-target:{digest}"
    def _query_target_decision_for_candidate(
        self,
        candidate: QueryTargetCandidate,
        *,
        index: int,
        status: str,
        summary: str,
        selection_mode: str = "automatic",
        peer_ready_requires_intent_review: bool = False,
        selection_caution: str | None = None,
        route_intent_review_candidate_indexes: list[int] | None = None,
    ) -> QueryTargetDecision:
        route_intent_indexes = list(route_intent_review_candidate_indexes or [])
        return QueryTargetDecision(
            status=status,
            summary=summary,
            candidate_index=index,
            candidate_path=candidate.candidate_path,
            candidate_path_status=candidate.candidate_path_status,
            direct_review_required=candidate.direct_review_required,
            selected_candidate_direct_clean=not candidate.direct_review_required,
            reason_codes=self._query_target_decision_reason_codes(
                candidate,
                status=status,
            ),
            selection_reason_codes=self._query_target_selection_reason_codes(
                candidate,
                status=status,
                selection_mode=selection_mode,
                peer_ready_requires_intent_review=(
                    peer_ready_requires_intent_review
                ),
                route_intent_review_candidate_indexes=route_intent_indexes,
            ),
            peer_ready_requires_intent_review=peer_ready_requires_intent_review,
            selection_caution=selection_caution,
            route_intent_review_candidate_indexes=route_intent_indexes,
            route_intent_caution=self._query_target_route_intent_caution(
                route_intent_indexes
            ),
        )
    def _query_target_route_intent_review_candidate_indexes(
        self,
        selected_candidate: QueryTargetCandidate | None,
        candidates: list[QueryTargetCandidate],
        candidate_indexes: Iterable[int],
    ) -> list[int]:
        if selected_candidate is None:
            return []
        priority_roles = {
            self.expand_iri("rc:ProductionRoute"),
            self.expand_iri("rc:CurrentRoute"),
            self.expand_iri("rc:CanonicalRoute"),
        }
        selected_roles = {role.iri for role in selected_candidate.route_roles}
        selected_priority_roles = selected_roles & priority_roles
        review_indexes: list[int] = []
        for index in candidate_indexes:
            if index < 0 or index >= len(candidates):
                continue
            candidate_priority_roles = (
                {role.iri for role in candidates[index].route_roles}
                & priority_roles
            )
            if candidate_priority_roles - selected_priority_roles:
                review_indexes.append(index)
        return review_indexes
    def _query_target_candidate_decision_rank(
        self,
        item: tuple[int, QueryTargetCandidate],
    ) -> tuple[int, int, int, int, int, int, int]:
        index, candidate = item
        path_status_rank = {
            "ready": 0,
            "orientation_only": 1,
            "unresolved": 2,
        }.get(candidate.candidate_path_status, 3)
        blocking_reasons = self._query_target_blocking_reasons(
            candidate.direct_review_reasons
        ) or self._query_target_blocking_reasons(candidate.review_reasons)
        severity_rank = self._query_target_blocking_severity_rank(blocking_reasons)
        return (
            path_status_rank,
            severity_rank,
            len(blocking_reasons),
            self._query_target_candidate_binding_count(candidate),
            self._query_target_candidate_relation_rank(candidate),
            self._query_target_candidate_source_rank(candidate),
            index,
        )
    @staticmethod
    def _query_target_candidate_binding_count(
        candidate: QueryTargetCandidate,
    ) -> int:
        template = candidate.candidate_path or candidate.template or ""
        return len(dict.fromkeys(re.findall(r"{([^{}]+)}", template)))
    @staticmethod
    def _query_target_candidate_relation_rank(
        candidate: QueryTargetCandidate,
    ) -> int:
        return 1 if candidate.relation_identifier is not None else 0
    @staticmethod
    def _query_target_candidate_source_rank(
        candidate: QueryTargetCandidate,
    ) -> int:
        return {
            "storage_access_location": 0,
            "dataset": 1,
            "partition_scheme": 2,
            "storage_access": 3,
        }.get(candidate.template_source, 4)
    def _query_template_has_applicable_non_database_candidate(
        self,
        dataset: DatasetDescription,
        *,
        template: str,
        template_source: str,
        source_resource: ResourceSummary,
    ) -> bool:
        if template_source in {"storage_access", "storage_access_location"}:
            return False
        for storage_access in dataset.storage_accesses:
            if self._is_database_storage(storage_access.storage_protocol):
                continue
            candidate_path, _composition = self._query_candidate_path(
                template,
                storage_access,
            )
            if candidate_path is None:
                continue
            if (
                self._query_storage_object_location_template_issue(
                    template=template,
                    template_source=template_source,
                    source_resource=source_resource,
                    storage_access=storage_access,
                )
                is not None
            ):
                continue
            if (
                self._query_candidate_metadata_issue(
                    template=template,
                    source_resource=source_resource,
                    storage_access=storage_access,
                )
                is not None
            ):
                continue
            if (
                self._query_candidate_path_extension_physical_layout_issue(
                    candidate_path=candidate_path,
                    template=template,
                    template_source=template_source,
                    source_resource=source_resource,
                    physical_layouts=dataset.physical_layouts,
                )
                is not None
            ):
                continue
            return True
        return False
    def _query_candidate_metadata_issue(
        self,
        *,
        template: str,
        source_resource: ResourceSummary,
        storage_access: StorageAccessDescription,
    ) -> QueryPlanningIssue | None:
        mismatch_reasons = self._candidate_storage_location_mismatch_reasons(
            storage_access,
            template,
        )
        if not mismatch_reasons:
            return None
        source_label = source_resource.label or source_resource.iri
        return QueryPlanningIssue(
            code="storage_protocol_location_mismatch",
            severity="warning",
            message=(
                "Storage access metadata conflicts with path "
                f"template from {source_label}: "
                + "; ".join(mismatch_reasons)
                + ". Record protocol-appropriate storage metadata "
                "or simplify the template before executable use."
            ),
            resource=self._summary_from_description(storage_access),
            details={
                "template": template,
                "template_source_resource_iri": source_resource.iri,
                "storage_access_iri": storage_access.iri,
                "storage_protocol_iri": (
                    storage_access.storage_protocol.iri
                    if storage_access.storage_protocol is not None
                    else None
                ),
                "storage_root": storage_access.storage_root,
                "bucket_name": storage_access.bucket_name,
                "key_prefix": storage_access.key_prefix,
                "mismatch_reasons": mismatch_reasons,
                "repair_hint": self._storage_protocol_location_repair_hint(
                    storage_access,
                    mismatch_reasons=mismatch_reasons,
                    template=template,
                    template_source_resource=source_resource,
                ),
            },
        )
    @staticmethod
    def _query_candidate_path_extension_format(
        candidate_path: str | None,
    ) -> str | None:
        if candidate_path is None:
            return None
        text = candidate_path.strip()
        if not text:
            return None
        text = re.split(r"[?#]", text, maxsplit=1)[0].rstrip("/")
        if not text:
            return None
        suffixes = [suffix.lower() for suffix in Path(text).suffixes]
        if not suffixes:
            return None
        compression_suffixes = {
            ".bz2",
            ".gz",
            ".gzip",
            ".snappy",
            ".zip",
            ".zst",
            ".zstd",
        }
        data_suffix = suffixes[-1]
        if data_suffix in compression_suffixes and len(suffixes) > 1:
            data_suffix = suffixes[-2]
        if data_suffix in {".parquet", ".pq"}:
            return "parquet"
        if data_suffix == ".csv":
            return "csv"
        return None
    def _query_target_candidate_metadata_issues(
        self,
        dataset: DatasetDescription,
        *,
        dataset_summary: ResourceSummary,
        direct_path_templates: list[str],
    ) -> list[QueryPlanningIssue]:
        if not dataset.storage_accesses:
            return []

        template_sources: list[tuple[str, str, ResourceSummary]] = [
            (template, "dataset", dataset_summary) for template in direct_path_templates
        ]
        template_sources.extend(
            (
                partition.path_template,
                "partition_scheme",
                self._summary_from_description(partition),
            )
            for partition in dataset.partition_schemes
            if partition.path_template is not None
        )

        issues: list[QueryPlanningIssue] = []
        for storage_access in dataset.storage_accesses:
            for template, template_source, source_resource in template_sources:
                object_location_issue = (
                    self._query_storage_object_location_template_issue(
                        template=template,
                        template_source=template_source,
                        source_resource=source_resource,
                        storage_access=storage_access,
                    )
                )
                if object_location_issue is not None:
                    issues.append(object_location_issue)
                relation_source_issue = None
                if not self._query_template_has_applicable_non_database_candidate(
                    dataset,
                    template=template,
                    template_source=template_source,
                    source_resource=source_resource,
                ):
                    relation_source_issue = (
                        self._query_database_relation_template_source_issue(
                            template=template,
                            template_source=template_source,
                            source_resource=source_resource,
                            storage_access=storage_access,
                        )
                    )
                if relation_source_issue is not None:
                    issues.append(relation_source_issue)
                issue = self._query_candidate_metadata_issue(
                    template=template,
                    source_resource=source_resource,
                    storage_access=storage_access,
                )
                if issue is not None:
                    issues.append(issue)
                candidate_path, _composition = self._query_candidate_path(
                    template,
                    storage_access,
                )
                format_issue = (
                    self._query_candidate_path_extension_physical_layout_issue(
                        candidate_path=candidate_path,
                        template=template,
                        template_source=template_source,
                        source_resource=source_resource,
                        physical_layouts=dataset.physical_layouts,
                    )
                )
                if format_issue is not None:
                    issues.append(format_issue)
            access_resource = self._summary_from_description(storage_access)
            for template in storage_access.path_templates:
                object_location_issue = (
                    self._query_storage_object_location_template_issue(
                        template=template,
                        template_source="storage_access",
                        source_resource=access_resource,
                        storage_access=storage_access,
                    )
                )
                if object_location_issue is not None:
                    issues.append(object_location_issue)
                issue = self._query_candidate_metadata_issue(
                    template=template,
                    source_resource=access_resource,
                    storage_access=storage_access,
                )
                if issue is not None:
                    issues.append(issue)
                candidate_path, _composition = self._query_candidate_path(
                    template,
                    storage_access,
                )
                format_issue = (
                    self._query_candidate_path_extension_physical_layout_issue(
                        candidate_path=candidate_path,
                        template=template,
                        template_source="storage_access",
                        source_resource=access_resource,
                        physical_layouts=dataset.physical_layouts,
                    )
                )
                if format_issue is not None:
                    issues.append(format_issue)
            if not template_sources and not storage_access.path_templates:
                issue = self._query_storage_access_location_kind_issue(storage_access)
                if issue is not None:
                    issues.append(issue)
                has_file_object_root = (
                    storage_access.storage_root is not None
                    and not self._is_database_storage(storage_access.storage_protocol)
                )
                if has_file_object_root:
                    format_issue = (
                        self._query_candidate_path_extension_physical_layout_issue(
                            candidate_path=storage_access.storage_root,
                            template=storage_access.storage_root,
                            template_source="storage_access_location",
                            source_resource=access_resource,
                            physical_layouts=dataset.physical_layouts,
                        )
                    )
                    if format_issue is not None:
                        issues.append(format_issue)
        return issues
    def _query_candidate_path_status(
        self,
        candidate_path: str | None,
        *,
        review_required: bool,
        review_reasons: list[QueryPlanningIssue],
    ) -> str:
        if candidate_path is None or any(
            reason.code == "missing_storage_location" for reason in review_reasons
        ):
            return "unresolved"
        if review_required:
            return "orientation_only"
        return "ready"
    def _query_candidate_path(
        self,
        template: str,
        storage_access: StorageAccessDescription | None,
    ) -> tuple[str | None, str]:
        template = template.strip()
        if not template:
            return None, "unresolved"
        if self._is_complete_path_template(template):
            return template, "template_as_returned"
        if storage_access is None:
            return template, "template_as_returned"

        storage_root = (storage_access.storage_root or "").strip()
        if storage_root:
            if self._template_starts_with_root(template, storage_root):
                return template, "template_as_returned"
            return self._join_path_template(storage_root, template), "storage_root_joined"

        bucket_name = (storage_access.bucket_name or "").strip().strip("/")
        if bucket_name and self._is_s3_storage(storage_access.storage_protocol):
            parts = [bucket_name]
            key_prefix = (storage_access.key_prefix or "").strip().strip("/")
            if key_prefix:
                parts.append(key_prefix)
            parts.append(template.strip("/"))
            return f"s3://{'/'.join(parts)}", "bucket_prefix_joined"

        key_prefix = (storage_access.key_prefix or "").strip()
        if key_prefix:
            return self._join_path_template(key_prefix, template), "key_prefix_joined"

        return template, "template_as_returned"
