"""Draft query plan construction and candidates.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via QueryPlansMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class QueryPlansMixin:
    @staticmethod
    def _query_plan_action_caution(
        *,
        caution: str | None,
        pending_repair_groups_present: bool,
    ) -> str | None:
        if not pending_repair_groups_present:
            return caution
        repair_caution = (
            "Pending query repair groups have non-skippable options; review "
            "suggested_repair_action_groups before treating draft_query_plan "
            "actions as unattended."
        )
        return f"{caution} {repair_caution}" if caution else repair_caution
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
                        "stage_query_storage_access_repair_candidate_arguments": (
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
                            "Copy these values into stage_query_storage_access_repair "
                            "only after reviewing the handle as a non-secret "
                            "database relation route."
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
            "stage_query_storage_access_repair_candidate_arguments": (
                storage_arguments
            ),
            "draft_query_evidence_storage_overlay_candidate_arguments": (
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
    def draft_query_plan(
        self,
        iri: str,
        *,
        graph: str | None = "map",
        engine: str = "duckdb",
        candidate_index: int | None = None,
        candidate_selector: str | None = None,
        storage_access_iri: str | None = None,
        physical_layout_iri: str | None = None,
        allow_context_blocked_candidate: bool = False,
    ) -> DraftQueryPlan:
        engine_value = engine.strip().lower()
        if engine_value != "duckdb":
            raise DoxaBaseError("draft_query_plan currently supports engine='duckdb'")
        context = self.describe_query_context(iri=iri, graph=graph)
        if context.readiness == "not_applicable_non_tabular_asset":
            return self._non_tabular_draft_query_plan(
                context,
                engine=engine_value,
                candidate_index=candidate_index,
                candidate_selector=candidate_selector,
                storage_access_iri=storage_access_iri,
                physical_layout_iri=physical_layout_iri,
                allow_context_blocked_candidate=allow_context_blocked_candidate,
            )
        selected_physical_layout, requested_physical_layout_iri = (
            self._draft_query_plan_selected_physical_layout(
                context,
                physical_layout_iri=physical_layout_iri,
            )
        )
        physical_layout_selected = requested_physical_layout_iri is not None
        effective_issues = self._draft_query_plan_effective_issues(
            context.issues,
            physical_layout_selected=physical_layout_selected,
        )
        (
            selected_candidate_index,
            selected_candidate,
            selection_mode,
            selection_status,
            selection_note,
            requested_storage_access_iri,
            requested_candidate_selector,
        ) = self._draft_query_plan_select_candidate(
            context,
            candidate_index=candidate_index,
            candidate_selector=candidate_selector,
            storage_access_iri=storage_access_iri,
            physical_layout_selected=physical_layout_selected,
        )
        selected_candidate = self._draft_query_plan_effective_layout_candidate(
            selected_candidate,
            physical_layout_selected=physical_layout_selected,
        )
        layout_mismatch_issue = (
            self._query_physical_layout_storage_protocol_mismatch_issue(
                selected_candidate,
                selected_physical_layout,
            )
        )
        if layout_mismatch_issue is not None:
            effective_issues = self._with_unique_query_issue(
                effective_issues,
                layout_mismatch_issue,
            )
            selected_candidate = self._query_candidate_with_added_issue(
                selected_candidate,
                layout_mismatch_issue,
            )
        layout_path_mismatch_issue = (
            self._query_selected_physical_layout_path_extension_issue(
                selected_candidate,
                selected_physical_layout,
            )
        )
        if layout_path_mismatch_issue is not None:
            effective_issues = self._with_unique_query_issue(
                effective_issues,
                layout_path_mismatch_issue,
            )
            selected_candidate = self._query_candidate_with_added_issue(
                selected_candidate,
                layout_path_mismatch_issue,
            )
        original_selected_candidate = selected_candidate
        (
            selected_candidate,
            context_blocked_candidate_used,
            context_blocking_reasons,
        ) = self._draft_query_plan_effective_candidate(
            context,
            selected_candidate,
            issues=effective_issues,
            selection_mode=selection_mode,
            allow_context_blocked_candidate=allow_context_blocked_candidate,
        )
        selected_decision = self._draft_query_plan_selected_decision(
            context,
            selected_candidate,
            selected_candidate_index=selected_candidate_index,
            selection_mode=selection_mode,
            selection_overridden=(
                selection_mode != "automatic" or physical_layout_selected
            ),
            context_blocked_candidate_used=context_blocked_candidate_used,
        )
        storage_access = self._draft_query_plan_storage_access(
            context,
            selected_candidate,
        )
        binding_requirements = self._draft_query_plan_binding_requirements(
            selected_candidate,
            columns=context.columns,
            partition_schemes=context.partition_schemes,
        )
        scan = self._draft_query_plan_scan(
            selected_candidate,
            dataset_verification_status=context.layout_verification_status,
            dataset_verification_note=context.layout_verification_note,
            partition_schemes=context.partition_schemes,
            physical_layouts=context.physical_layouts,
            selected_physical_layout=selected_physical_layout,
            physical_layout_selected=physical_layout_selected,
            storage_accesses=context.storage_accesses,
            engine=engine_value,
        )
        storage_environment = self._draft_query_plan_storage_environment(
            selected_candidate,
            storage_access,
            engine=engine_value,
        )
        review_gate = self._draft_query_plan_review_gate(
            context,
            selected_candidate,
            original_selected_candidate=original_selected_candidate,
            selected_decision=selected_decision,
            scan=scan,
            issues=effective_issues,
            storage_environment=storage_environment,
            binding_requirements=binding_requirements,
            selection_overridden=(
                selection_mode != "automatic" or physical_layout_selected
            ),
            allow_context_blocked_candidate=allow_context_blocked_candidate,
            context_blocked_candidate_used=context_blocked_candidate_used,
            context_blocking_reasons=context_blocking_reasons,
        )
        scan = replace(
            scan,
            execution_attempt_ready=review_gate.ready_for_execution_attempt,
            primary_execution_attempt_blocking_reason_code=(
                review_gate.primary_execution_attempt_blocking_reason_code
            ),
            execution_attempt_blocking_reason_codes=list(
                review_gate.execution_attempt_blocking_reason_codes
            ),
        )
        handoff_kind = self._draft_query_plan_handoff_kind(
            selected_candidate,
            scan=scan,
            binding_requirements=binding_requirements,
            storage_environment=storage_environment,
            review_gate=review_gate,
        )
        ready_candidate_indexes = self._query_ready_candidate_indexes(
            context.query_target_candidates
        )
        direct_clean_candidate_indexes = self._query_direct_clean_candidate_indexes(
            context.query_target_candidates
        )
        unselected_ready_candidate_indexes = [
            index
            for index in ready_candidate_indexes
            if index != selected_candidate_index
        ]
        unselected_direct_clean_candidate_indexes = [
            index
            for index in direct_clean_candidate_indexes
            if index != selected_candidate_index
        ]
        peer_ready_requires_intent_review = bool(unselected_ready_candidate_indexes)
        route_intent_review_candidate_indexes = (
            self._query_target_route_intent_review_candidate_indexes(
                selected_candidate,
                context.query_target_candidates,
                unselected_direct_clean_candidate_indexes,
            )
        )
        selection_reason_codes = self._query_target_selection_reason_codes(
            selected_candidate,
            status=selected_decision.status,
            selection_mode=selection_mode,
            peer_ready_requires_intent_review=peer_ready_requires_intent_review,
            route_intent_review_candidate_indexes=(
                route_intent_review_candidate_indexes
            ),
        )
        selection_caution = self._query_target_selection_caution(
            unselected_ready_candidate_indexes,
            selection_mode=selection_mode,
            route_intent_review_candidate_indexes=(
                route_intent_review_candidate_indexes
            ),
        )
        selected_candidate_note = self._draft_query_plan_selected_candidate_note(
            selected_candidate,
            selected_candidate_index,
            handoff_kind=handoff_kind,
            review_gate=review_gate,
            context_blocking_reasons=context_blocking_reasons,
        )
        source_context = DraftQueryPlanSourceContext(
            api="DoxaBase.describe_query_context",
            readiness=context.readiness,
            readiness_note=context.readiness_note,
            query_target_decision=context.query_target_decision,
            selected_candidate_index=selected_candidate_index,
            candidate_count=len(context.query_target_candidates),
            ready_candidate_indexes=ready_candidate_indexes,
            unselected_ready_candidate_indexes=unselected_ready_candidate_indexes,
            direct_clean_candidate_indexes=direct_clean_candidate_indexes,
            unselected_direct_clean_candidate_indexes=(
                unselected_direct_clean_candidate_indexes
            ),
            selection_mode=selection_mode,
            requested_candidate_index=candidate_index,
            requested_candidate_selector=requested_candidate_selector,
            requested_storage_access_iri=requested_storage_access_iri,
            requested_physical_layout_iri=requested_physical_layout_iri,
            selected_candidate_selector=(
                selected_candidate.candidate_selector
                if selected_candidate is not None
                else None
            ),
            selection_status=selection_status,
            selection_note=selection_note,
            selected_candidate_note=selected_candidate_note,
            allow_context_blocked_candidate=allow_context_blocked_candidate,
            selection_reason_codes=selection_reason_codes,
            peer_ready_requires_intent_review=peer_ready_requires_intent_review,
            selection_caution=selection_caution,
            route_intent_review_candidate_indexes=(
                route_intent_review_candidate_indexes
            ),
            route_intent_caution=self._query_target_route_intent_caution(
                route_intent_review_candidate_indexes
            ),
        )
        required_bindings = [binding.name for binding in binding_requirements]
        handoff_summary = self._draft_query_plan_handoff_summary(
            handoff_kind=handoff_kind,
            source_context=source_context,
            scan=scan,
            review_gate=review_gate,
            required_bindings=required_bindings,
            issues=effective_issues,
            analysis_warnings=context.analysis_warnings,
            caveats=context.caveats,
        )
        return DraftQueryPlan(
            helper="draft_query_plan",
            mode="non_executed_review_draft",
            handoff_kind=handoff_kind,
            handoff_summary=handoff_summary,
            engine=DraftQueryPlanEngine(
                name=engine_value,
                source="caller_requested_target_engine",
            ),
            dataset=context.dataset,
            source_context=source_context,
            selected_candidate=selected_candidate,
            scan=scan,
            required_bindings=required_bindings,
            binding_requirements=binding_requirements,
            binding_note=(
                "Bindings are placeholder names parsed from the selected path "
                "template. When a selected partition template has matching "
                "partition metadata, binding rows include the likely partition "
                "column and granularity. Non-partition templates may carry "
                "best-effort candidate column matches by placeholder name; "
                "DoxaBase still does not infer execution-time values."
            ),
            storage_environment=storage_environment,
            review_gate=review_gate,
            issues=effective_issues,
            analysis_warnings=context.analysis_warnings,
            caveats=context.caveats,
            upstream_caveats=context.upstream_caveats,
            planning_notes=[
                *context.planning_notes,
                (
                    "This draft is not executable code and does not resolve "
                    "endpoint profiles, credentials, object existence, or "
                    "runtime settings."
                ),
            ],
        )
    def _non_tabular_draft_query_plan(
        self,
        context: QueryPlanningContext,
        *,
        engine: str,
        candidate_index: int | None,
        candidate_selector: str | None,
        storage_access_iri: str | None,
        physical_layout_iri: str | None,
        allow_context_blocked_candidate: bool,
    ) -> DraftQueryPlan:
        reason_code = "non_tabular_asset_query_not_applicable"
        scan = DraftQueryPlanScan(
            function=None,
            uri_template=None,
            relation_identifier=None,
            connection_reference=None,
            file_format=None,
            compression=None,
            candidate_path_status=None,
            dataset_verification_status=context.layout_verification_status,
            dataset_verification_note=context.layout_verification_note,
            template=None,
            template_source=None,
            template_source_resource=None,
            template_source_verification_status=None,
            template_source_verification_note=None,
            template_lineage=None,
            composition=None,
            physical_layout=None,
            physical_layout_selection_note=None,
            non_executed_note=(
                "No scan is drafted because the dataset is not typed as "
                "rc:Table."
            ),
            execution_attempt_ready=False,
            primary_execution_attempt_blocking_reason_code=reason_code,
            execution_attempt_blocking_reason_codes=[reason_code],
        )
        storage_environment = DraftQueryPlanStorageEnvironment(
            storage_protocol=None,
            storage_root=None,
            bucket_name=None,
            key_prefix=None,
            region=None,
            endpoint_profile=None,
            credential_reference=None,
            access_mode=None,
            path_style_access=None,
            requires_endpoint_profile=False,
            runtime_resolution_required=False,
            duckdb_settings_from_context=[],
            runtime_resolution_note=(
                "No runtime storage environment is drafted for a non-tabular "
                "asset."
            ),
        )
        review_gate = DraftQueryPlanReviewGate(
            executable_without_review=False,
            runtime_resolution_required=False,
            binding_values_required=False,
            ready_for_execution_attempt=False,
            status="not_applicable_non_tabular_asset",
            direct_review_required=None,
            candidate_path_status=None,
            blocking_reason_codes=[reason_code],
            execution_attempt_blocking_reason_codes=[reason_code],
            primary_execution_attempt_blocking_reason_code=reason_code,
            all_issue_codes=self._query_issue_codes(context.issues),
            reason_codes=[reason_code],
            review_note=(
                "DoxaBase does not draft table query plans for map assets that "
                "are not typed as rc:Table. Inspect the asset with resource or "
                "context-slice handoffs instead."
            ),
            selection_overridden=(
                candidate_index is not None
                or candidate_selector is not None
                or storage_access_iri is not None
                or physical_layout_iri is not None
            ),
            context_blocked_candidate_allowed=allow_context_blocked_candidate,
            context_blocked_candidate_used=False,
            direct_blocking_reason_codes=[reason_code],
            context_blocking_reason_codes=[],
        )
        source_context = DraftQueryPlanSourceContext(
            api="DoxaBase.describe_query_context",
            readiness=context.readiness,
            readiness_note=context.readiness_note,
            query_target_decision=context.query_target_decision,
            selected_candidate_index=None,
            candidate_count=0,
            ready_candidate_indexes=[],
            unselected_ready_candidate_indexes=[],
            direct_clean_candidate_indexes=[],
            unselected_direct_clean_candidate_indexes=[],
            selection_mode="not_applicable",
            requested_candidate_index=candidate_index,
            requested_candidate_selector=candidate_selector,
            requested_storage_access_iri=storage_access_iri,
            requested_physical_layout_iri=physical_layout_iri,
            selected_candidate_selector=None,
            selection_status="not_applicable_non_tabular_asset",
            selection_note=(
                "Candidate selection is not applicable because the dataset "
                "is not typed as rc:Table."
            ),
            selected_candidate_note=(
                "No query target candidate is selected for a non-tabular "
                "asset."
            ),
            allow_context_blocked_candidate=allow_context_blocked_candidate,
            selection_reason_codes=["not_applicable_non_tabular_asset"],
            peer_ready_requires_intent_review=False,
            selection_caution=None,
        )
        handoff_summary = self._draft_query_plan_handoff_summary(
            handoff_kind="not_applicable_non_tabular_asset",
            source_context=source_context,
            scan=scan,
            review_gate=review_gate,
            required_bindings=[],
            issues=context.issues,
            analysis_warnings=context.analysis_warnings,
            caveats=context.caveats,
        )
        return DraftQueryPlan(
            helper="draft_query_plan",
            mode="non_executed_review_draft",
            handoff_kind="not_applicable_non_tabular_asset",
            handoff_summary=handoff_summary,
            engine=DraftQueryPlanEngine(
                name=engine,
                source="caller_requested_target_engine",
            ),
            dataset=context.dataset,
            source_context=source_context,
            selected_candidate=None,
            scan=scan,
            required_bindings=[],
            binding_requirements=[],
            binding_note=(
                "No path-template bindings are inferred because no table query "
                "plan is drafted for this non-tabular asset."
            ),
            storage_environment=storage_environment,
            review_gate=review_gate,
            issues=context.issues,
            analysis_warnings=context.analysis_warnings,
            caveats=context.caveats,
            upstream_caveats=context.upstream_caveats,
            planning_notes=[
                *context.planning_notes,
                (
                    "This draft is intentionally not a query handoff. Model an "
                    "explicit table/queryable relation first if query planning "
                    "is genuinely intended."
                ),
            ],
        )
    @staticmethod
    def _query_ready_candidate_indexes(
        candidates: list[QueryTargetCandidate],
    ) -> list[int]:
        return [
            index
            for index, candidate in enumerate(candidates)
            if candidate.candidate_path_status == "ready"
            and not candidate.direct_review_required
        ]
    @staticmethod
    def _query_direct_clean_candidate_indexes(
        candidates: list[QueryTargetCandidate],
    ) -> list[int]:
        return [
            index
            for index, candidate in enumerate(candidates)
            if not candidate.direct_review_required
        ]
    def _draft_query_plan_select_candidate(
        self,
        context: QueryPlanningContext,
        *,
        candidate_index: int | None,
        candidate_selector: str | None,
        storage_access_iri: str | None,
        physical_layout_selected: bool = False,
    ) -> tuple[
        int | None,
        QueryTargetCandidate | None,
        str,
        str,
        str,
        str | None,
        str | None,
    ]:
        explicit_selectors = [
            name
            for name, value in (
                ("candidate_index", candidate_index),
                ("candidate_selector", candidate_selector),
                ("storage_access_iri", storage_access_iri),
            )
            if value is not None
        ]
        if len(explicit_selectors) > 1:
            raise DoxaBaseError(
                "Pass only one explicit query target selector: "
                + ", ".join(explicit_selectors)
                + "."
            )

        if candidate_index is not None:
            if candidate_index < 0 or candidate_index >= len(
                context.query_target_candidates
            ):
                raise DoxaBaseError(
                    "candidate_index must point into query_target_candidates; "
                    f"got {candidate_index} for "
                    f"{len(context.query_target_candidates)} candidate(s)."
                )
            return (
                candidate_index,
                context.query_target_candidates[candidate_index],
                "candidate_index",
                "matched",
                f"Caller selected candidate {candidate_index} by candidate_index.",
                None,
                None,
            )

        if candidate_selector is not None:
            selector_value = candidate_selector.strip()
            if not selector_value:
                raise DoxaBaseError("candidate_selector must not be empty.")
            matches = [
                (index, candidate)
                for index, candidate in enumerate(context.query_target_candidates)
                if candidate.candidate_selector == selector_value
            ]
            if not matches:
                snippets = "; ".join(
                    self._draft_query_plan_candidate_selection_snippet(
                        index,
                        candidate,
                    )
                    for index, candidate in enumerate(
                        context.query_target_candidates[:5]
                    )
                )
                if len(context.query_target_candidates) > 5:
                    snippets = f"{snippets}; ..."
                raise DoxaBaseError(
                    "candidate_selector did not match any query target "
                    f"candidate: {selector_value}. Available candidates: "
                    f"{snippets}"
                )
            if len(matches) > 1:
                indexes = ", ".join(str(index) for index, _candidate in matches)
                snippets = "; ".join(
                    self._draft_query_plan_candidate_selection_snippet(
                        index,
                        candidate,
                    )
                    for index, candidate in matches
                )
                raise DoxaBaseError(
                    "candidate_selector matched multiple query target "
                    f"candidates ({indexes}): {snippets}."
                )
            selected_index, selected_candidate = matches[0]
            return (
                selected_index,
                selected_candidate,
                "candidate_selector",
                "matched",
                (
                    "Caller selected candidate_selector "
                    f"{selector_value}, matching candidate {selected_index}."
                ),
                None,
                selector_value,
            )

        if storage_access_iri is not None:
            storage_access_value = self._required_iri(
                "storage_access_iri",
                storage_access_iri,
            )
            matches = [
                (index, candidate)
                for index, candidate in enumerate(context.query_target_candidates)
                if candidate.storage_access is not None
                and candidate.storage_access.iri == storage_access_value
            ]
            if not matches:
                raise DoxaBaseError(
                    "storage_access_iri did not match any query target "
                    f"candidate: {storage_access_value}"
                )
            if len(matches) > 1:
                indexes = ", ".join(str(index) for index, _candidate in matches)
                snippets = "; ".join(
                    self._draft_query_plan_candidate_selection_snippet(
                        index,
                        candidate,
                    )
                    for index, candidate in matches
                )
                layout_note = (
                    " physical_layout_iri was matched, but storage_access_iri "
                    "still identifies multiple query target candidates; pass "
                    "candidate_selector for the stable path/relation, or "
                    "candidate_index for a response-local fallback."
                    if physical_layout_selected
                    else ""
                )
                raise DoxaBaseError(
                    "storage_access_iri matched multiple query target candidates "
                    f"({indexes}): {snippets}. Pass candidate_selector for a "
                    f"stable selection or candidate_index for an exact "
                    f"response-local fallback.{layout_note}"
                )
            selected_index, selected_candidate = matches[0]
            return (
                selected_index,
                selected_candidate,
                "storage_access_iri",
                "matched",
                (
                    "Caller selected storage_access_iri "
                    f"{storage_access_value}, matching candidate {selected_index}."
                ),
                storage_access_value,
                None,
            )

        decision = context.query_target_decision
        if (
            decision.candidate_index is not None
            and 0 <= decision.candidate_index < len(context.query_target_candidates)
        ):
            return (
                decision.candidate_index,
                context.query_target_candidates[decision.candidate_index],
                "automatic",
                "automatic",
                (
                    "Automatic query_target_decision selected candidate "
                    f"{decision.candidate_index}."
                ),
                None,
                None,
            )
        return (
            None,
            None,
            "automatic",
            "automatic",
            "Automatic query_target_decision did not select a candidate.",
            None,
            None,
        )
    def _draft_query_plan_candidate_selection_snippet(
        self,
        index: int,
        candidate: QueryTargetCandidate,
    ) -> str:
        source_label = candidate.source_resource.label or self._local_name(
            candidate.source_resource.iri
        )
        storage_label = None
        if candidate.storage_access is not None:
            storage_label = candidate.storage_access.label or self._local_name(
                candidate.storage_access.iri
            )
        parts = [
            f"candidate {index}",
            f"candidate_selector={candidate.candidate_selector!r}",
            f"template_source={candidate.template_source}",
            f"source={source_label!r}",
            f"status={candidate.candidate_path_status}",
        ]
        if candidate.candidate_path is not None:
            parts.append(f"candidate_path={candidate.candidate_path!r}")
        if candidate.relation_identifier is not None:
            parts.append(f"relation_identifier={candidate.relation_identifier!r}")
        if candidate.connection_reference is not None:
            parts.append(f"connection_reference={candidate.connection_reference!r}")
        if candidate.template is not None:
            parts.append(f"template={candidate.template!r}")
        if candidate.route_roles:
            route_roles = ", ".join(
                role.label or self._local_name(role.iri) for role in candidate.route_roles
            )
            parts.append(f"route_roles={route_roles!r}")
        if storage_label is not None:
            parts.append(f"storage={storage_label!r}")
        return " ".join(parts)
    def _draft_query_plan_effective_candidate(
        self,
        context: QueryPlanningContext,
        selected_candidate: QueryTargetCandidate | None,
        *,
        issues: list[QueryPlanningIssue],
        selection_mode: str,
        allow_context_blocked_candidate: bool,
    ) -> tuple[QueryTargetCandidate | None, bool, list[QueryPlanningIssue]]:
        if selected_candidate is None:
            return None, False, []
        context_blockers = self._query_target_context_blocking_reasons(
            selected_candidate.review_reasons
        )
        sibling_metadata_blockers = (
            self._draft_query_plan_sibling_candidate_metadata_context_blockers(
                context,
                selected_candidate,
                issues=issues,
            )
        )
        context_blocking_reasons = list(context_blockers)
        if not context_blocking_reasons and sibling_metadata_blockers:
            context_blocking_reasons = [
                self._draft_query_plan_sibling_context_blocker_issue(
                    context,
                    sibling_metadata_blockers,
                )
            ]
        if (
            not allow_context_blocked_candidate
            or selected_candidate.direct_review_required
            or selection_mode == "automatic"
        ):
            return selected_candidate, False, context_blocking_reasons

        if context_blockers:
            direct_review_reasons = list(selected_candidate.direct_review_reasons)
            direct_review_required = any(
                reason.severity in {"error", "warning"}
                for reason in direct_review_reasons
            )
            review_required = direct_review_required
            return (
                replace(
                    selected_candidate,
                    review_required=review_required,
                    review_reasons=direct_review_reasons,
                    direct_review_required=direct_review_required,
                    candidate_path_status=self._query_candidate_path_status(
                        selected_candidate.candidate_path,
                        review_required=review_required,
                        review_reasons=direct_review_reasons,
                    ),
                ),
                True,
                context_blocking_reasons,
            )

        if selection_mode != "automatic" and sibling_metadata_blockers:
            return selected_candidate, True, context_blocking_reasons

        return selected_candidate, False, context_blocking_reasons
    def _draft_query_plan_sibling_candidate_metadata_context_blockers(
        self,
        context: QueryPlanningContext,
        selected_candidate: QueryTargetCandidate,
        *,
        issues: list[QueryPlanningIssue],
    ) -> list[QueryPlanningIssue]:
        if (
            context.readiness == "ready_for_query_planning"
            or selected_candidate.direct_review_required
            or selected_candidate.candidate_path_status != "ready"
        ):
            return []
        blockers = self._query_target_blocking_reasons(issues)
        if not blockers or not all(
            self._is_candidate_metadata_issue(issue) for issue in blockers
        ):
            return []
        return blockers
    def _draft_query_plan_sibling_context_blocker_issue(
        self,
        context: QueryPlanningContext,
        blockers: list[QueryPlanningIssue],
    ) -> QueryPlanningIssue:
        resource_iris = [
            issue.resource.iri
            for issue in blockers
            if issue.resource is not None
        ]
        return QueryPlanningIssue(
            code="query_context_has_other_blockers",
            severity=(
                "error"
                if any(issue.severity == "error" for issue in blockers)
                else "warning"
            ),
            message=(
                "Overall query context has candidate-metadata blocker(s) on "
                "other query target candidates; inspect context.issues before "
                "executing this candidate."
            ),
            resource=context.dataset,
            details={
                "excluded_blocker_count": len(blockers),
                "excluded_blocker_codes": self._query_issue_codes(blockers),
                "excluded_blocker_resource_iris": list(dict.fromkeys(resource_iris)),
            },
        )
    def _draft_query_plan_selected_decision(
        self,
        context: QueryPlanningContext,
        selected_candidate: QueryTargetCandidate | None,
        *,
        selected_candidate_index: int | None,
        selection_mode: str,
        selection_overridden: bool,
        context_blocked_candidate_used: bool,
    ) -> QueryTargetDecision:
        if (
            selection_mode == "automatic"
            and not selection_overridden
            and not context_blocked_candidate_used
        ):
            return context.query_target_decision
        if selected_candidate is None or selected_candidate_index is None:
            return QueryTargetDecision(
                status="no_candidate",
                summary=(
                    "No query target candidate is available for this "
                    "draft_query_plan call."
                ),
                candidate_index=None,
                candidate_path=None,
                candidate_path_status=None,
                direct_review_required=None,
                selected_candidate_direct_clean=None,
                reason_codes=[],
            )

        if (
            selected_candidate.candidate_path_status == "ready"
            and not selected_candidate.review_required
        ):
            status = "ready"
            state_summary = "is ready for query planning"
        elif (
            selected_candidate.review_required
            and not selected_candidate.direct_review_required
        ):
            status = "context_blocked"
            state_summary = (
                "has no direct warning or error, but broader context has "
                "blockers"
            )
        else:
            status = "candidate_needs_review"
            state_summary = "needs review before executable query use"

        selector_summary = (
            "Automatic selection"
            if selection_mode == "automatic"
            else f"Explicit {selection_mode} selection"
        )
        if context_blocked_candidate_used:
            state_summary = (
                "is treated as direct-clean for this draft because "
                "allow_context_blocked_candidate=True ignored sibling-only "
                "context blockers"
            )
        ready_candidate_indexes = self._query_ready_candidate_indexes(
            context.query_target_candidates
        )
        direct_clean_candidate_indexes = self._query_direct_clean_candidate_indexes(
            context.query_target_candidates
        )
        unselected_ready_candidate_indexes = [
            index
            for index in ready_candidate_indexes
            if index != selected_candidate_index
        ]
        unselected_direct_clean_candidate_indexes = [
            index
            for index in direct_clean_candidate_indexes
            if index != selected_candidate_index
        ]
        route_intent_review_candidate_indexes = (
            self._query_target_route_intent_review_candidate_indexes(
                selected_candidate,
                context.query_target_candidates,
                unselected_direct_clean_candidate_indexes,
            )
        )
        return self._query_target_decision_for_candidate(
            selected_candidate,
            index=selected_candidate_index,
            status=status,
            summary=(
                f"{selector_summary} chose candidate {selected_candidate_index}, "
                f"which {state_summary}."
            ),
            selection_mode=selection_mode,
            peer_ready_requires_intent_review=bool(
                unselected_ready_candidate_indexes
            ),
            selection_caution=self._query_target_selection_caution(
                unselected_ready_candidate_indexes,
                selection_mode=selection_mode,
                route_intent_review_candidate_indexes=(
                    route_intent_review_candidate_indexes
                ),
            ),
            route_intent_review_candidate_indexes=(
                route_intent_review_candidate_indexes
            ),
        )
    @staticmethod
    def _draft_query_plan_selected_candidate_note(
        selected_candidate: QueryTargetCandidate | None,
        selected_candidate_index: int | None,
        *,
        handoff_kind: str,
        review_gate: DraftQueryPlanReviewGate,
        context_blocking_reasons: list[QueryPlanningIssue],
    ) -> str:
        if selected_candidate is None or selected_candidate_index is None:
            return "No query target candidate is selected."
        direct_state = (
            "direct-clean"
            if selected_candidate.direct_review_required is False
            else "review-gated"
        )
        route_label = handoff_kind.replace("_", " ")
        note = (
            f"Selected candidate {selected_candidate_index} is a "
            f"{direct_state} {route_label}."
        )
        if review_gate.context_blocked_candidate_used:
            sibling_codes: list[str] = []
            for reason in context_blocking_reasons:
                details = reason.details or {}
                excluded_codes = details.get("excluded_blocker_codes")
                if isinstance(excluded_codes, list):
                    sibling_codes.extend(str(code) for code in excluded_codes)
            sibling_codes = list(dict.fromkeys(sibling_codes))
            if sibling_codes:
                return (
                    f"{note} Sibling/context metadata still has "
                    f"{', '.join(sibling_codes)}; these codes remain in "
                    "review_gate.all_issue_codes."
                )
            if review_gate.context_blocking_reason_codes:
                return (
                    f"{note} Context blockers still have "
                    f"{', '.join(review_gate.context_blocking_reason_codes)}; "
                    "see review_gate.all_issue_codes."
                )
        if review_gate.blocking_reason_codes:
            return (
                f"{note} Blocking reason codes: "
                f"{', '.join(review_gate.blocking_reason_codes)}."
            )
        return note
    def _draft_query_plan_effective_layout_candidate(
        self,
        selected_candidate: QueryTargetCandidate | None,
        *,
        physical_layout_selected: bool,
    ) -> QueryTargetCandidate | None:
        if selected_candidate is None or not physical_layout_selected:
            return selected_candidate
        review_reasons = self._without_query_issue_code(
            selected_candidate.review_reasons,
            "ambiguous_physical_layout",
        )
        direct_review_reasons = self._without_query_issue_code(
            selected_candidate.direct_review_reasons,
            "ambiguous_physical_layout",
        )
        review_required = any(
            reason.severity in {"error", "warning"} for reason in review_reasons
        )
        direct_review_required = any(
            reason.severity in {"error", "warning"}
            for reason in direct_review_reasons
        )
        return replace(
            selected_candidate,
            review_required=review_required,
            review_reasons=review_reasons,
            direct_review_required=direct_review_required,
            direct_review_reasons=direct_review_reasons,
            candidate_path_status=self._query_candidate_path_status(
                selected_candidate.candidate_path,
                review_required=review_required,
                review_reasons=review_reasons,
            ),
        )
    def _query_candidate_with_added_issue(
        self,
        candidate: QueryTargetCandidate | None,
        issue: QueryPlanningIssue,
    ) -> QueryTargetCandidate | None:
        if candidate is None:
            return None
        review_reasons = self._with_unique_query_issue(
            candidate.review_reasons,
            issue,
        )
        direct_review_reasons = self._with_unique_query_issue(
            candidate.direct_review_reasons,
            issue,
        )
        review_required = any(
            reason.severity in {"error", "warning"} for reason in review_reasons
        )
        direct_review_required = any(
            reason.severity in {"error", "warning"}
            for reason in direct_review_reasons
        )
        return replace(
            candidate,
            review_required=review_required,
            review_reasons=review_reasons,
            direct_review_required=direct_review_required,
            direct_review_reasons=direct_review_reasons,
            candidate_path_status=self._query_candidate_path_status(
                candidate.candidate_path,
                review_required=review_required,
                review_reasons=review_reasons,
            ),
        )
    def _draft_query_plan_effective_issues(
        self,
        issues: list[QueryPlanningIssue],
        *,
        physical_layout_selected: bool,
    ) -> list[QueryPlanningIssue]:
        if not physical_layout_selected:
            return issues
        return self._without_query_issue_code(issues, "ambiguous_physical_layout")
    def _draft_query_plan_scan(
        self,
        selected_candidate: QueryTargetCandidate | None,
        *,
        dataset_verification_status: ResourceSummary | None,
        dataset_verification_note: str | None,
        partition_schemes: list[PartitionDescription],
        physical_layouts: list[PhysicalLayoutDescription],
        selected_physical_layout: PhysicalLayoutDescription | None,
        physical_layout_selected: bool,
        storage_accesses: list[StorageAccessDescription],
        engine: str,
    ) -> DraftQueryPlanScan:
        selected_layout = selected_physical_layout or (
            self._unique_physical_layout_for_query_plan(physical_layouts)
        )
        file_format = self._draft_query_plan_resource_label(
            selected_layout.file_format if selected_layout is not None else None
        )
        compression = self._draft_query_plan_resource_label(
            selected_layout.compression_codec if selected_layout is not None else None
        )
        template_status, template_note = self._draft_query_plan_template_verification(
            selected_candidate,
            dataset_verification_status=dataset_verification_status,
            dataset_verification_note=dataset_verification_note,
            partition_schemes=partition_schemes,
            storage_accesses=storage_accesses,
        )
        scan_function = (
            None
            if selected_candidate is not None
            and self._is_database_storage(selected_candidate.storage_protocol)
            else self._draft_query_plan_scan_function(engine, file_format)
        )
        database_storage = (
            selected_candidate is not None
            and self._is_database_storage(selected_candidate.storage_protocol)
        )
        return DraftQueryPlanScan(
            function=scan_function,
            uri_template=(
                selected_candidate.candidate_path
                if selected_candidate is not None and not database_storage
                else None
            ),
            relation_identifier=(
                selected_candidate.relation_identifier
                if selected_candidate is not None and database_storage
                else None
            ),
            connection_reference=(
                selected_candidate.connection_reference
                if selected_candidate is not None and database_storage
                else None
            ),
            file_format=file_format,
            compression=compression,
            candidate_path_status=(
                selected_candidate.candidate_path_status
                if selected_candidate is not None
                else None
            ),
            dataset_verification_status=dataset_verification_status,
            dataset_verification_note=dataset_verification_note,
            template=selected_candidate.template if selected_candidate is not None else None,
            template_source=(
                selected_candidate.template_source
                if selected_candidate is not None
                else None
            ),
            template_source_resource=(
                selected_candidate.source_resource
                if selected_candidate is not None
                else None
            ),
            template_source_verification_status=template_status,
            template_source_verification_note=template_note,
            template_lineage=self._draft_query_plan_template_lineage(
                selected_candidate,
                verification_status=template_status,
                verification_note=template_note,
            ),
            composition=(
                selected_candidate.composition if selected_candidate is not None else None
            ),
            physical_layout=(
                self._summary_from_description(selected_layout)
                if selected_layout is not None
                else None
            ),
            physical_layout_selection_note=(
                "Caller selected this physical layout for the draft query plan."
                if physical_layout_selected
                else (
                    "A single linked physical layout signature was selected "
                    "automatically."
                    if selected_layout is not None
                    else (
                        "No unambiguous physical layout was selected; scan "
                        "function inference is withheld."
                    )
                )
            ),
            non_executed_note=(
                "Review-only draft; do not run without resolving runtime "
                "configuration and reviewing issues, verification notes, and "
                "analysis caveats."
            ),
        )
    def _draft_query_plan_template_verification(
        self,
        selected_candidate: QueryTargetCandidate | None,
        *,
        dataset_verification_status: ResourceSummary | None,
        dataset_verification_note: str | None,
        partition_schemes: list[PartitionDescription],
        storage_accesses: list[StorageAccessDescription],
    ) -> tuple[ResourceSummary | None, str | None]:
        if selected_candidate is None:
            return None, None
        if selected_candidate.template_source == "dataset":
            return dataset_verification_status, dataset_verification_note
        if selected_candidate.template_source == "partition_scheme":
            for partition in partition_schemes:
                if partition.iri == selected_candidate.source_resource.iri:
                    return (
                        partition.layout_verification_status,
                        partition.layout_verification_note,
                    )
        if selected_candidate.template_source in {
            "storage_access",
            "storage_access_location",
        }:
            for storage_access in storage_accesses:
                if storage_access.iri == selected_candidate.source_resource.iri:
                    return (
                        storage_access.layout_verification_status,
                        storage_access.layout_verification_note,
                    )
        return None, None
    @staticmethod
    def _draft_query_plan_resource_label(resource: ResourceSummary | None) -> str | None:
        if resource is None:
            return None
        return resource.label or resource.iri
    @staticmethod
    def _draft_query_plan_scan_function(
        engine: str,
        file_format: str | None,
    ) -> str | None:
        if engine != "duckdb" or file_format is None:
            return None
        normalized = file_format.lower()
        if "parquet" in normalized:
            return "read_parquet"
        if "csv" in normalized:
            return "read_csv_auto"
        return None
    def _draft_query_plan_binding_requirements(
        self,
        selected_candidate: QueryTargetCandidate | None,
        *,
        columns: list[ColumnDescription],
        partition_schemes: list[PartitionDescription],
    ) -> list[DraftQueryPlanBinding]:
        if selected_candidate is None:
            return []
        template = self._draft_query_plan_binding_source_text(selected_candidate)
        names = list(dict.fromkeys(re.findall(r"{([^{}]+)}", template or "")))
        partition = self._draft_query_plan_binding_partition(
            selected_candidate,
            partition_schemes,
        )

        def binding_for(name: str) -> DraftQueryPlanBinding:
            partition_column = (
                self._draft_query_plan_partition_column_for_binding(
                    name,
                    partition,
                )
                if partition is not None
                else None
            )
            candidate_column_matches = (
                []
                if partition is not None and partition_column is not None
                else self._draft_query_plan_column_matches_for_binding(
                    name,
                    columns,
                )
            )
            candidate_column_match_status = (
                "not_applicable"
                if partition is not None and partition_column is not None
                else self._draft_query_plan_column_match_status(
                    candidate_column_matches
                )
            )
            return DraftQueryPlanBinding(
                name=name,
                source="path_template_placeholder",
                source_text=template,
                required=True,
                derivation_status="not_inferred",
                derivation_note=self._draft_query_plan_binding_derivation_note(
                    name,
                    partition=partition,
                    partition_column=partition_column,
                    candidate_column_matches=candidate_column_matches,
                    candidate_column_match_status=(
                        candidate_column_match_status
                    ),
                ),
                binding_kind=(
                    "partition_template_placeholder"
                    if partition is not None
                    else "path_template_placeholder"
                ),
                partition_scheme=(
                    self._summary_from_description(partition)
                    if partition is not None
                    else None
                ),
                partition_column=partition_column,
                partition_granularity=(
                    partition.granularity if partition is not None else None
                ),
                candidate_column_matches=candidate_column_matches,
                candidate_column_match_status=candidate_column_match_status,
            )

        return [
            binding_for(name)
            for name in names
        ]
    @staticmethod
    def _draft_query_plan_binding_source_text(
        selected_candidate: QueryTargetCandidate,
    ) -> str | None:
        return selected_candidate.candidate_path or selected_candidate.template
    @staticmethod
    def _draft_query_plan_binding_partition(
        selected_candidate: QueryTargetCandidate,
        partition_schemes: list[PartitionDescription],
    ) -> PartitionDescription | None:
        if selected_candidate.template_source == "partition_scheme":
            for partition in partition_schemes:
                if partition.iri == selected_candidate.source_resource.iri:
                    return partition
            return None
        matching_partitions = [
            partition
            for partition in partition_schemes
            if partition.path_template is not None
            and partition.path_template.strip() == selected_candidate.template.strip()
        ]
        if len(matching_partitions) == 1:
            return matching_partitions[0]
        return None
    def _draft_query_plan_column_matches_for_binding(
        self,
        name: str,
        columns: list[ColumnDescription],
    ) -> list[DraftQueryPlanBindingColumnMatch]:
        placeholder = self._normalized_binding_name(name)
        if not placeholder:
            return []
        exact_matches: list[DraftQueryPlanBindingColumnMatch] = []
        suffix_matches: list[DraftQueryPlanBindingColumnMatch] = []
        for column in columns:
            candidates = [
                ("column_name", column.column_name),
                ("label", column.label),
                ("local_name", self._local_name(column.iri)),
            ]
            exact = self._first_binding_column_match(
                placeholder,
                column,
                candidates,
                match_kind="exact_name",
                confidence="high",
            )
            if exact is not None:
                exact_matches.append(exact)
                continue
            suffix = self._first_binding_column_match(
                placeholder,
                column,
                candidates,
                match_kind="suffix_name",
                confidence="medium",
            )
            if suffix is not None:
                suffix_matches.append(suffix)
        return exact_matches or suffix_matches
    @staticmethod
    def _draft_query_plan_column_match_status(
        candidate_column_matches: list[DraftQueryPlanBindingColumnMatch],
    ) -> str:
        if not candidate_column_matches:
            return "none"
        if len(candidate_column_matches) == 1:
            return "single"
        return "ambiguous"
    def _draft_query_plan_partition_column_for_binding(
        self,
        name: str,
        partition: PartitionDescription,
    ) -> ResourceSummary | None:
        placeholder = self._normalized_binding_name(name)
        if not placeholder:
            return None
        exact_matches: list[ResourceSummary] = []
        suffix_matches: list[ResourceSummary] = []
        for column in partition.partition_columns:
            candidate_names = [
                column.column_name,
                column.label,
                self._local_name(column.iri),
            ]
            normalized_names = {
                normalized
                for value in candidate_names
                if (normalized := self._normalized_binding_name(value))
            }
            if placeholder in normalized_names:
                exact_matches.append(column)
            elif any(
                self._binding_name_has_suffix(normalized, placeholder)
                for normalized in normalized_names
            ):
                suffix_matches.append(column)
        for matches in (exact_matches, suffix_matches):
            unique = {column.iri: column for column in matches}
            if len(unique) == 1:
                return next(iter(unique.values()))
        return None
    def _draft_query_plan_binding_derivation_note(
        self,
        name: str,
        *,
        partition: PartitionDescription | None,
        partition_column: ResourceSummary | None,
        candidate_column_matches: list[DraftQueryPlanBindingColumnMatch],
        candidate_column_match_status: str,
    ) -> str:
        base_note = (
            "Supply this value explicitly or derive it in the runtime query "
            "layer after review; DoxaBase has not inferred a type, dependency, "
            "or default value for this placeholder."
        )
        if partition is None:
            if candidate_column_matches:
                match_names = ", ".join(
                    match.column.label
                    or match.column.column_name
                    or match.column.iri
                    for match in candidate_column_matches
                )
                if candidate_column_match_status == "ambiguous":
                    return (
                        f"{base_note} Candidate column hint(s): {match_names}. "
                        "Multiple candidate columns matched this placeholder; "
                        "review which source column, if any, should supply the "
                        "runtime value."
                    )
                return (
                    f"{base_note} Candidate column hint(s): {match_names}. "
                    "These are best-effort placeholder/name matches, not "
                    "inferred runtime binding values."
                )
            return base_note
        details: list[str] = []
        if partition_column is not None:
            partition_column_label = (
                partition_column.label
                or partition_column.column_name
                or partition_column.iri
            )
            details.append(
                f"likely partition column {partition_column_label}"
            )
        if partition.granularity is not None:
            details.append(
                "partition scheme granularity "
                f"{partition.granularity.label or partition.granularity.iri}"
            )
        candidate_note = ""
        if candidate_column_matches:
            match_names = ", ".join(
                match.column.label or match.column.column_name or match.column.iri
                for match in candidate_column_matches
            )
            if candidate_column_match_status == "ambiguous":
                candidate_note = (
                    f" Candidate column hint(s): {match_names}. Multiple "
                    "candidate columns matched this placeholder; review which "
                    "source column, if any, should supply the runtime value."
                )
            else:
                candidate_note = (
                    f" Candidate column hint(s): {match_names}. These are "
                    "best-effort placeholder/name matches, not inferred "
                    "runtime binding values."
                )
        if not details:
            return (
                f"{base_note} The selected template comes from partition scheme "
                f"{partition.label or partition.iri}.{candidate_note}"
            )
        return (
            f"{base_note} The selected template comes from partition scheme "
            f"{partition.label or partition.iri}; metadata indicates "
            f"{'; '.join(details)}.{candidate_note}"
        )
    def _draft_query_plan_storage_environment(
        self,
        selected_candidate: QueryTargetCandidate | None,
        storage_access: StorageAccessDescription | None,
        *,
        engine: str,
    ) -> DraftQueryPlanStorageEnvironment:
        duckdb_settings: list[str] = []
        path_style_access = (
            selected_candidate.path_style_access
            if selected_candidate is not None
            else None
        )
        region = storage_access.region if storage_access is not None else None
        if engine == "duckdb":
            if path_style_access is not None:
                duckdb_settings.append(
                    f"s3_url_style={'path' if path_style_access else 'vhost'}"
                )
            if region is not None:
                duckdb_settings.append(f"s3_region={region}")
        endpoint_profile = (
            selected_candidate.endpoint_profile
            if selected_candidate is not None
            else None
        )
        credential_reference = (
            selected_candidate.credential_reference
            if selected_candidate is not None
            else None
        )
        requires_endpoint_profile = (
            selected_candidate.requires_endpoint_profile
            if selected_candidate is not None
            else False
        )
        unresolved_s3_access = (
            selected_candidate is not None
            and any(
                reason.code == "s3_access_resolution_unrecorded"
                for reason in selected_candidate.review_reasons
            )
        )
        database_storage = (
            selected_candidate is not None
            and self._is_database_storage(selected_candidate.storage_protocol)
        )
        runtime_resolution_required = bool(
            database_storage
            or endpoint_profile
            or credential_reference
            or requires_endpoint_profile
            or unresolved_s3_access
        )
        if unresolved_s3_access:
            runtime_resolution_note = (
                "Record or resolve the S3 endpoint profile, credential reference, "
                "region, and object access in the local runtime before running any "
                "query."
            )
        elif runtime_resolution_required:
            if database_storage:
                runtime_resolution_note = (
                    "Resolve the recorded database endpoint profile or credential "
                    "reference in the local runtime, and verify connection, "
                    "schema, table, or source access before running any query."
                )
            else:
                runtime_resolution_note = (
                    "Resolve the recorded endpoint profile or credential reference "
                    "in the local runtime, and verify object access before running "
                    "any query."
                )
        elif database_storage:
            runtime_resolution_note = (
                "Database relation handoff requires an external runtime to "
                "resolve the connection, schema, table, or source access before "
                "running any query."
            )
        else:
            runtime_resolution_note = (
                "No endpoint or credential profile is recorded or required by "
                "the graph; still verify local paths or remote object existence "
                "before running any query."
            )
        return DraftQueryPlanStorageEnvironment(
            storage_protocol=(
                selected_candidate.storage_protocol
                if selected_candidate is not None
                else None
            ),
            storage_root=(
                selected_candidate.storage_root
                if selected_candidate is not None
                else None
            ),
            bucket_name=(
                selected_candidate.bucket_name
                if selected_candidate is not None
                else None
            ),
            key_prefix=(
                selected_candidate.key_prefix
                if selected_candidate is not None
                else None
            ),
            region=region,
            endpoint_profile=endpoint_profile,
            credential_reference=credential_reference,
            access_mode=storage_access.access_mode if storage_access is not None else None,
            path_style_access=path_style_access,
            requires_endpoint_profile=requires_endpoint_profile,
            runtime_resolution_required=runtime_resolution_required,
            duckdb_settings_from_context=duckdb_settings,
            runtime_resolution_note=runtime_resolution_note,
        )
    def _draft_query_plan_review_gate(
        self,
        context: QueryPlanningContext,
        selected_candidate: QueryTargetCandidate | None,
        *,
        original_selected_candidate: QueryTargetCandidate | None,
        selected_decision: QueryTargetDecision,
        scan: DraftQueryPlanScan,
        issues: list[QueryPlanningIssue],
        storage_environment: DraftQueryPlanStorageEnvironment,
        binding_requirements: list[DraftQueryPlanBinding],
        selection_overridden: bool,
        allow_context_blocked_candidate: bool,
        context_blocked_candidate_used: bool,
        context_blocking_reasons: list[QueryPlanningIssue],
    ) -> DraftQueryPlanReviewGate:
        blocking_reason_codes = self._draft_query_plan_blocking_reason_codes(
            context,
            selected_candidate,
            selected_decision=selected_decision,
            scan=scan,
            issues=issues,
            context_blocked_candidate_used=context_blocked_candidate_used,
        )
        context_metadata_ready = (
            context.readiness == "ready_for_query_planning"
            or context_blocked_candidate_used
            or not self._query_blocking_issue_codes(issues)
        )
        executable_without_review = (
            context_metadata_ready
            and selected_decision.status == "ready"
            and selected_decision.candidate_path_status == "ready"
            and selected_decision.direct_review_required is False
            and not blocking_reason_codes
        )
        binding_values_required = any(
            binding.required for binding in binding_requirements
        )
        execution_attempt_blocking_reason_codes = (
            self._draft_query_plan_execution_attempt_blocking_reason_codes(
                blocking_reason_codes=blocking_reason_codes,
                runtime_resolution_required=(
                    storage_environment.runtime_resolution_required
                ),
                binding_values_required=binding_values_required,
            )
        )
        direct_blocking_reason_codes = self._query_issue_codes(
            self._query_target_blocking_reasons(
                selected_candidate.direct_review_reasons
                if selected_candidate is not None
                else []
            )
        )
        context_blocking_reason_codes = self._query_issue_codes(
            context_blocking_reasons
            or self._query_target_context_blocking_reasons(
                original_selected_candidate.review_reasons
                if original_selected_candidate is not None
                else []
            )
        )
        return DraftQueryPlanReviewGate(
            executable_without_review=executable_without_review,
            runtime_resolution_required=(
                storage_environment.runtime_resolution_required
            ),
            binding_values_required=binding_values_required,
            ready_for_execution_attempt=(
                executable_without_review
                and not storage_environment.runtime_resolution_required
                and not binding_values_required
            ),
            status=selected_decision.status,
            direct_review_required=selected_decision.direct_review_required,
            candidate_path_status=selected_decision.candidate_path_status,
            blocking_reason_codes=blocking_reason_codes,
            execution_attempt_blocking_reason_codes=(
                execution_attempt_blocking_reason_codes
            ),
            primary_execution_attempt_blocking_reason_code=(
                execution_attempt_blocking_reason_codes[0]
                if execution_attempt_blocking_reason_codes
                else None
            ),
            all_issue_codes=self._query_issue_codes(issues),
            reason_codes=blocking_reason_codes,
            review_note=(
                "This helper drafts a non-executed plan. Review selected "
                "candidate reasons, physical metadata issues, verification "
                "notes, and analysis warnings before execution."
                if selected_candidate is not None
                else "No query target candidate is available."
            ),
            selection_overridden=selection_overridden,
            context_blocked_candidate_allowed=allow_context_blocked_candidate,
            context_blocked_candidate_used=context_blocked_candidate_used,
            direct_blocking_reason_codes=direct_blocking_reason_codes,
            context_blocking_reason_codes=context_blocking_reason_codes,
        )
    @staticmethod
    def _draft_query_plan_execution_attempt_blocking_reason_codes(
        *,
        blocking_reason_codes: list[str],
        runtime_resolution_required: bool,
        binding_values_required: bool,
    ) -> list[str]:
        codes = list(blocking_reason_codes)
        if runtime_resolution_required:
            codes.append("runtime_resolution_required")
        if binding_values_required:
            codes.append("binding_values_required")
        return list(dict.fromkeys(codes))
    def _draft_query_plan_blocking_reason_codes(
        self,
        context: QueryPlanningContext,
        selected_candidate: QueryTargetCandidate | None,
        *,
        selected_decision: QueryTargetDecision,
        scan: DraftQueryPlanScan,
        issues: list[QueryPlanningIssue],
        context_blocked_candidate_used: bool,
    ) -> list[str]:
        codes = list(selected_decision.reason_codes)
        if (
            not codes
            and context.readiness != "ready_for_query_planning"
            and not context_blocked_candidate_used
        ):
            issue_codes = self._query_blocking_issue_codes(issues)
            if selected_candidate is None:
                codes.extend(issue_codes)
            elif issue_codes and selected_decision.direct_review_required is False:
                codes.append("query_context_has_other_blockers")
            else:
                codes.extend(issue_codes)
        if (
            selected_candidate is not None
            and selected_decision.candidate_path_status == "ready"
            and scan.function is None
            and not self._is_database_storage(selected_candidate.storage_protocol)
        ):
            codes.append("scan_function_not_inferred")
        return list(dict.fromkeys(codes))
    @staticmethod
    def _query_plan_required_binding_names(
        binding_requirements: list[DraftQueryPlanBinding],
    ) -> list[str]:
        return [
            binding.name
            for binding in binding_requirements
            if binding.required
        ]
    @staticmethod
    def _query_plan_required_binding_details(
        binding_requirements: list[DraftQueryPlanBinding],
    ) -> list[dict[str, Any]]:
        return [
            {
                "name": binding.name,
                "binding_kind": binding.binding_kind,
                "partition_scheme": binding.partition_scheme,
                "partition_column": binding.partition_column,
                "partition_granularity": binding.partition_granularity,
                "candidate_column_match_status": (
                    binding.candidate_column_match_status
                ),
            }
            for binding in binding_requirements
            if binding.required
        ]
    def _query_plan_action_binding_examples(
        self,
        candidate: QueryTargetCandidate,
        binding_requirements: list[DraftQueryPlanBinding],
    ) -> list[dict[str, Any]]:
        partition_bindings = [
            binding
            for binding in binding_requirements
            if binding.required
            and binding.binding_kind == "partition_template_placeholder"
        ]
        if not partition_bindings:
            return []
        example_values = {
            binding.name: self._query_plan_action_binding_example_value(binding)
            for binding in partition_bindings
        }
        rendered_template = self._query_plan_action_render_binding_example(
            self._draft_query_plan_binding_source_text(candidate),
            example_values,
        )
        examples: list[dict[str, Any]] = []
        for binding in partition_bindings:
            example = {
                "binding": binding.name,
                "binding_kind": binding.binding_kind,
                "example_value": example_values[binding.name],
                "rendered_template": rendered_template,
            }
            if rendered_template is not None:
                example["example"] = (
                    f"{binding.name}={example_values[binding.name]!r} -> "
                    f"{rendered_template}"
                )
            else:
                example["example"] = (
                    f"{binding.name}={example_values[binding.name]!r}"
                )
            examples.append(example)
        return examples
    @staticmethod
    def _query_plan_action_binding_example_summary(
        binding_examples: list[dict[str, Any]],
    ) -> str | None:
        if not binding_examples:
            return None
        assignments = ", ".join(
            f"{example['binding']}={example['example_value']!r}"
            for example in binding_examples
        )
        rendered_template = binding_examples[0].get("rendered_template")
        if isinstance(rendered_template, str) and rendered_template:
            return f"{assignments} -> {rendered_template}"
        return assignments
    def _query_plan_action_binding_example_value(
        self,
        binding: DraftQueryPlanBinding,
    ) -> str:
        hints = [binding.name]
        if binding.partition_column is not None:
            hints.extend(
                value
                for value in (
                    binding.partition_column.column_name,
                    binding.partition_column.label,
                    self._local_name(binding.partition_column.iri),
                )
                if value
            )
        if binding.partition_granularity is not None:
            hints.extend(
                value
                for value in (
                    binding.partition_granularity.label,
                    self._local_name(binding.partition_granularity.iri),
                )
                if value
            )
        normalized = self._normalized_binding_name(" ".join(hints))
        tokens = set(normalized.split("_"))
        if {"date", "dt"} & tokens or normalized.endswith("_date"):
            return "2026-06-30"
        if "year" in tokens or normalized.endswith("_year"):
            return "2026"
        if "month" in tokens or normalized.endswith("_month"):
            return "06"
        if "day" in tokens or normalized.endswith("_day"):
            return "30"
        if "hour" in tokens or normalized.endswith("_hour"):
            return "13"
        placeholder = self._normalized_binding_name(binding.name).upper()
        return f"REVIEWED_{placeholder or 'VALUE'}"
    @staticmethod
    def _query_plan_action_render_binding_example(
        source_text: str | None,
        example_values: Mapping[str, str],
    ) -> str | None:
        if source_text is None:
            return None
        rendered = source_text
        for name, value in example_values.items():
            rendered = rendered.replace("{" + name + "}", value)
        return rendered
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
    def _is_candidate_metadata_issue(self, issue: QueryPlanningIssue) -> bool:
        if issue.code in {
            "database_relation_template_source_mismatch",
            "physical_layout_path_extension_mismatch",
            "storage_object_location_has_path_template",
        }:
            return True
        return (
            issue.code == "storage_protocol_location_mismatch"
            and issue.message.startswith(
                "Storage access metadata conflicts with path template from "
            )
        )
    def _is_complete_path_template(self, template: str) -> bool:
        return bool(re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", template)) or template.startswith(
            "/"
        )
    def _template_starts_with_root(self, template: str, storage_root: str) -> bool:
        normalized_template = template.strip("/")
        normalized_root = storage_root.strip("/")
        if not normalized_root:
            return False
        return (
            normalized_template == normalized_root
            or normalized_template.startswith(f"{normalized_root}/")
        )
    def _join_path_template(self, root: str, template: str) -> str:
        cleaned_root = root.rstrip("/")
        cleaned_template = template.lstrip("/")
        if not cleaned_root:
            return f"/{cleaned_template}"
        return f"{cleaned_root}/{cleaned_template}"
    def _is_s3_storage(self, storage_protocol: ResourceSummary | None) -> bool:
        if storage_protocol is None:
            return False
        return storage_protocol.iri == self.expand_iri("rc:S3CompatibleStorage")
    def _is_https_storage(self, storage_protocol: ResourceSummary | None) -> bool:
        if storage_protocol is None:
            return False
        return storage_protocol.iri == self.expand_iri("rc:HTTPSStorage")
    def _is_database_storage(self, storage_protocol: ResourceSummary | None) -> bool:
        if storage_protocol is None:
            return False
        return storage_protocol.iri == self.expand_iri("rc:DatabaseStorage")
    def _is_local_filesystem_storage(
        self,
        storage_protocol: ResourceSummary | None,
    ) -> bool:
        if storage_protocol is None:
            return False
        return storage_protocol.iri == self.expand_iri("rc:LocalFilesystemStorage")
    def _storage_root_scheme(self, storage_root: str | None) -> str | None:
        if storage_root is None:
            return None
        match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):", storage_root.strip())
        if match is None:
            return None
        return match.group(1).lower()
    def _path_template_scheme(self, template: str | None) -> str | None:
        if template is None:
            return None
        match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*)://", template.strip())
        if match is None:
            return None
        return match.group(1).lower()
    def _is_s3_scheme(self, scheme: str | None) -> bool:
        return scheme in {"s3", "s3a", "s3n"}
    def _s3_template_location(
        self,
        template: str,
    ) -> tuple[str, str] | None:
        match = re.match(
            r"^(?:s3|s3a|s3n)://([^/]+)(?:/(.*))?$",
            template.strip(),
            flags=re.IGNORECASE,
        )
        if match is None:
            return None
        return match.group(1), (match.group(2) or "").strip("/")
    def _s3_template_under_root(
        self,
        template: str,
        storage_root: str | None,
    ) -> bool | None:
        template_location = self._s3_template_location(template)
        if template_location is None or not storage_root:
            return None
        root_location = self._s3_template_location(storage_root)
        if root_location is None:
            return None
        template_bucket, template_key = template_location
        root_bucket, root_key = root_location
        if template_bucket != root_bucket:
            return False
        if not root_key:
            return True
        return template_key == root_key or template_key.startswith(f"{root_key}/")
    def _looks_like_absolute_local_path(self, storage_root: str | None) -> bool:
        if storage_root is None:
            return False
        text = storage_root.strip()
        return text.startswith("/") or bool(re.match(r"^[A-Za-z]:[\\/]", text))
    def _local_path_under_root(
        self,
        template: str,
        storage_root: str | None,
    ) -> bool | None:
        if not (
            self._looks_like_absolute_local_path(template)
            and self._looks_like_absolute_local_path(storage_root)
        ):
            return None
        template_text = template.strip()
        root_text = (storage_root or "").strip()
        if re.match(r"^[A-Za-z]:[\\/]", template_text) or re.match(
            r"^[A-Za-z]:[\\/]",
            root_text,
        ):
            template_norm = ntpath.normcase(ntpath.normpath(template_text))
            root_norm = ntpath.normcase(ntpath.normpath(root_text))
            try:
                return ntpath.commonpath([template_norm, root_norm]) == root_norm
            except ValueError:
                return False

        template_norm = posixpath.normpath(template_text)
        root_norm = posixpath.normpath(root_text)
        try:
            return posixpath.commonpath([template_norm, root_norm]) == root_norm
        except ValueError:
            return False
    def _s3_access_resolution_unrecorded(
        self,
        access: StorageAccessDescription,
    ) -> bool:
        if not self._is_s3_storage(access.storage_protocol):
            return False
        if access.endpoint_profile or access.credential_reference or access.region:
            return False
        if access.bucket_name or access.key_prefix:
            return True
        if self._is_s3_scheme(self._storage_root_scheme(access.storage_root)):
            return True
        return any(
            self._is_s3_scheme(self._path_template_scheme(template))
            for template in access.path_templates
        )
    def _s3_credential_reference_not_recorded(
        self,
        access: StorageAccessDescription,
    ) -> bool:
        if not self._is_s3_storage(access.storage_protocol):
            return False
        if access.credential_reference:
            return False
        if self._s3_access_resolution_unrecorded(access):
            return False
        return bool(
            access.endpoint_profile
            or access.region
            or access.bucket_name
            or access.key_prefix
            or self._is_s3_scheme(self._storage_root_scheme(access.storage_root))
            or any(
                self._is_s3_scheme(self._path_template_scheme(template))
                for template in access.path_templates
            )
        )
    def _candidate_storage_location_mismatch_reasons(
        self,
        access: StorageAccessDescription,
        template: str,
    ) -> list[str]:
        reasons: list[str] = []
        scheme = self._path_template_scheme(template)
        if access.storage_protocol is not None:
            if self._is_s3_storage(access.storage_protocol):
                if self._looks_like_absolute_local_path(template):
                    reasons.append("path template looks like a local filesystem path")
                elif scheme is not None and not self._is_s3_scheme(scheme):
                    reasons.append(
                        f"path template scheme '{scheme}' does not look like S3"
                    )
            elif self._is_https_storage(access.storage_protocol):
                if scheme not in {None, "http", "https"} or (
                    scheme is None and self._looks_like_absolute_local_path(template)
                ):
                    reasons.append("path template does not look like an HTTP(S) URL")
            elif self._is_local_filesystem_storage(access.storage_protocol):
                if scheme in {"s3", "s3a", "s3n", "http", "https"}:
                    reasons.append(
                        "path template looks remote for local filesystem access"
                    )
                local_under_root = self._local_path_under_root(
                    template,
                    access.storage_root,
                )
                if local_under_root is False:
                    reasons.append(
                        "absolute local path template is outside recorded "
                        f"storage_root '{access.storage_root}'"
                    )

        s3_location = self._s3_template_location(template)
        if s3_location is not None:
            template_bucket, template_key = s3_location
            under_s3_root = self._s3_template_under_root(
                template,
                access.storage_root,
            )
            if under_s3_root is False:
                reasons.append(
                    "complete S3 path template is outside recorded "
                    f"storage_root '{access.storage_root}'"
                )
            bucket_name = (access.bucket_name or "").strip().strip("/")
            if bucket_name and template_bucket != bucket_name:
                reasons.append(
                    "complete S3 path template bucket does not match recorded "
                    f"bucket_name '{bucket_name}'"
                )
            key_prefix = (access.key_prefix or "").strip().strip("/")
            if (
                key_prefix
                and template_key
                and template_key != key_prefix
                and not template_key.startswith(f"{key_prefix}/")
            ):
                reasons.append(
                    "complete S3 path template key does not start with recorded "
                    f"key_prefix '{key_prefix}'"
                )

        key_prefix = (access.key_prefix or "").strip().strip("/")
        normalized_template = template.strip().strip("/")
        if (
            key_prefix
            and scheme is None
            and not self._looks_like_absolute_local_path(template)
            and (
                normalized_template == key_prefix
                or normalized_template.startswith(f"{key_prefix}/")
            )
        ):
            reasons.append(
                f"path template appears to repeat recorded key_prefix '{key_prefix}'"
            )

        return reasons
    def _storage_protocol_location_mismatch_reasons(
        self,
        access: StorageAccessDescription,
    ) -> list[str]:
        reasons: list[str] = []
        if access.storage_protocol is None:
            return reasons
        if not self._is_s3_storage(access.storage_protocol) and (
            access.bucket_name or access.key_prefix
        ):
            reasons.append("bucket/prefix metadata is recorded for a non-S3 protocol")

        scheme = self._storage_root_scheme(access.storage_root)
        if self._is_s3_storage(access.storage_protocol):
            if self._looks_like_absolute_local_path(access.storage_root):
                reasons.append("storage_root looks like a local filesystem path")
            root_location = self._s3_template_location(access.storage_root or "")
            if root_location is not None:
                root_bucket, root_key = root_location
                bucket_name = (access.bucket_name or "").strip().strip("/")
                if bucket_name and root_bucket != bucket_name:
                    reasons.append(
                        "S3 storage_root bucket does not match recorded "
                        f"bucket_name '{bucket_name}'"
                    )
                key_prefix = (access.key_prefix or "").strip().strip("/")
                if (
                    key_prefix
                    and root_key
                    and root_key != key_prefix
                    and not root_key.startswith(f"{key_prefix}/")
                ):
                    reasons.append(
                        "S3 storage_root key does not start with recorded "
                        f"key_prefix '{key_prefix}'"
                    )
        elif self._is_https_storage(access.storage_protocol):
            if scheme in {"s3", "s3a", "s3n", "file"} or (
                scheme is None
                and self._looks_like_absolute_local_path(access.storage_root)
            ):
                reasons.append("storage_root does not look like an HTTP(S) root")
        elif self._is_local_filesystem_storage(access.storage_protocol):
            if scheme in {"s3", "s3a", "s3n", "http", "https"}:
                reasons.append("storage_root looks remote for local filesystem access")
        return reasons
    def _query_planning_issues(
        self,
        dataset: DatasetDescription,
    ) -> list[QueryPlanningIssue]:
        issues: list[QueryPlanningIssue] = []
        if self._dataset_description_is_analysis_view(dataset):
            return issues

        def add_issue(
            code: str,
            severity: str,
            message: str,
            resource: ResourceSummary | None = None,
            details: dict[str, Any] | None = None,
        ) -> None:
            issues.append(
                QueryPlanningIssue(
                    code=code,
                    severity=severity,
                    message=message,
                    resource=resource,
                    details=details,
                )
            )

        dataset_resource = ResourceSummary(
            iri=dataset.iri,
            label=dataset.label or self._local_name(dataset.iri),
            description=dataset.description,
        )
        has_storage_root_location = any(
            access.storage_root for access in dataset.storage_accesses
        )
        if not dataset.path_templates and not has_storage_root_location:
            add_issue(
                "missing_path_template",
                "error",
                "No dataset, storage, or partition path template is recorded.",
                dataset_resource,
            )
        if not dataset.storage_accesses:
            add_issue(
                "missing_storage_access",
                "error",
                "No storage access resource is linked to the dataset.",
                dataset_resource,
                self._missing_storage_access_details(
                    dataset,
                    dataset_resource=dataset_resource,
                ),
            )
        for access in dataset.storage_accesses:
            access_resource = self._summary_from_description(access)
            if access.storage_protocol is None:
                add_issue(
                    "missing_storage_protocol",
                    "error",
                    "Storage access does not declare a storage protocol.",
                    access_resource,
                )
            has_location = any(
                [
                    access.storage_root,
                    access.bucket_name,
                    access.key_prefix,
                    access.path_templates,
                ]
            )
            if not has_location:
                add_issue(
                    "missing_storage_location",
                    "error",
                    "Storage access does not include a root, bucket, prefix, or path template.",
                    access_resource,
                )
            if self._s3_access_resolution_unrecorded(access):
                add_issue(
                    "s3_access_resolution_unrecorded",
                    "warning",
                    "S3-compatible access records S3 location metadata but no endpoint profile, credential reference, or region.",
                    access_resource,
                )
            elif self._s3_credential_reference_not_recorded(access):
                add_issue(
                    "s3_credential_reference_not_recorded",
                    "info",
                    (
                        "S3-compatible access has enough non-secret endpoint "
                        "or location context for query planning, but no "
                        "credential_reference marker is recorded. If credentials "
                        "are intentionally omitted, record "
                        "credential_reference='external:intentionally-unrecorded'; "
                        "otherwise record a reviewed non-secret profile/env "
                        "marker such as 'profile:<name>' or 'env:<VAR_NAME>'."
                    ),
                    access_resource,
                    {
                        "storage_access_iri": access.iri,
                        "storage_protocol_iri": (
                            access.storage_protocol.iri
                            if access.storage_protocol is not None
                            else None
                        ),
                        "endpoint_profile": access.endpoint_profile,
                        "bucket_name": access.bucket_name,
                        "key_prefix": access.key_prefix,
                        "region": access.region,
                        "credential_reference": access.credential_reference,
                        "recommended_omitted_marker": (
                            "external:intentionally-unrecorded"
                        ),
                    },
                )
            location_mismatch_reasons = (
                self._storage_protocol_location_mismatch_reasons(access)
            )
            if location_mismatch_reasons:
                add_issue(
                    "storage_protocol_location_mismatch",
                    "warning",
                    (
                        "Storage access metadata conflicts with its protocol: "
                        + "; ".join(location_mismatch_reasons)
                        + ". Record a protocol-appropriate storage root, URL, "
                        "or connection reference before executable use."
                    ),
                    access_resource,
                    {
                        "storage_access_iri": access.iri,
                        "storage_protocol_iri": (
                            access.storage_protocol.iri
                            if access.storage_protocol is not None
                            else None
                        ),
                        "storage_root": access.storage_root,
                        "bucket_name": access.bucket_name,
                        "key_prefix": access.key_prefix,
                        "mismatch_reasons": location_mismatch_reasons,
                        "repair_hint": (
                            self._storage_protocol_location_repair_hint(
                                access,
                                mismatch_reasons=location_mismatch_reasons,
                            )
                        ),
                    },
                )
            self._add_layout_status_issue(
                issues,
                status=access.layout_verification_status,
                note=access.layout_verification_note,
                resource=access_resource,
                context="storage access",
                include_missing_status=has_location,
            )
        if not dataset.physical_layouts:
            add_issue(
                "missing_physical_layout",
                "warning",
                "No physical layout resource is linked to the dataset.",
                dataset_resource,
                (
                    self._missing_physical_layout_details(dataset)
                    if dataset.storage_accesses
                    else None
                ),
            )
        ambiguous_layout_issue = self._ambiguous_physical_layout_issue(
            dataset.physical_layouts,
            dataset_resource=dataset_resource,
        )
        if ambiguous_layout_issue is not None:
            issues.append(ambiguous_layout_issue)
        for layout in dataset.physical_layouts:
            layout_resource = self._summary_from_description(layout)
            if layout.file_format is None:
                add_issue(
                    "missing_file_format",
                    "warning",
                    "Physical layout does not declare a file format.",
                    layout_resource,
                )
            self._add_layout_status_issue(
                issues,
                status=layout.layout_verification_status,
                note=layout.layout_verification_note,
                resource=layout_resource,
                context="physical layout",
                include_missing_status=layout.file_format is not None,
            )
        self._add_layout_status_issue(
            issues,
            status=dataset.layout_verification_status,
            note=dataset.layout_verification_note,
            resource=dataset_resource,
            context="dataset layout",
            include_missing_status=bool(dataset.path_templates),
        )
        for partition in dataset.partition_schemes:
            self._add_layout_status_issue(
                issues,
                status=partition.layout_verification_status,
                note=partition.layout_verification_note,
                resource=self._summary_from_description(partition),
                context="partition scheme",
                include_missing_status=partition.path_template is not None,
            )

        return self._sort_query_planning_issues(issues)
    def _missing_storage_existing_access_candidates(
        self,
        dataset: DatasetDescription,
        *,
        limit: int,
    ) -> tuple[list[dict[str, Any]], int]:
        data_graphs = self._expand_graphs(["map"])
        lookup_graphs = self._lookup_graphs(data_graphs)
        dataset_templates = set(dataset.path_templates)
        dataset_tokens = self._missing_storage_candidate_tokens(
            [
                dataset.label,
                self._local_name(dataset.iri),
                *dataset.path_templates,
            ]
        )
        pending_staged_links = self._pending_staged_storage_access_links(
            dataset.iri,
        )
        candidates: list[tuple[int, str, str, dict[str, Any]]] = []
        for access_iri in self._subjects(
            data_graphs,
            "rdf:type",
            self.expand_iri("rc:StorageAccess"),
        ):
            access = self._describe_storage_access(
                access_iri,
                data_graphs,
                lookup_graphs,
            )
            match_reasons: list[str] = []
            score = 0
            if dataset_templates and dataset_templates & set(access.path_templates):
                match_reasons.append("shares_dataset_path_template")
                score += 100
            if access.storage_protocol is not None:
                match_reasons.append("declares_storage_protocol")
                score += 20
            if any(
                [
                    access.storage_root,
                    access.bucket_name,
                    access.key_prefix,
                    access.path_templates,
                ]
            ):
                match_reasons.append("has_location_metadata")
                score += 20
            if access.layout_verification_status is not None:
                match_reasons.append("has_layout_verification_status")
                score += 10
            label = access.label or self._local_name(access.iri)
            access_tokens = self._missing_storage_candidate_tokens(
                [
                    label,
                    self._local_name(access.iri),
                    access.storage_root,
                    access.bucket_name,
                    access.key_prefix,
                    *access.path_templates,
                ]
            )
            exact_token_matches = sorted(dataset_tokens & access_tokens)
            strong_exact_token_matches = [
                token
                for token in exact_token_matches
                if token not in MISSING_STORAGE_GENERIC_TOKENS
            ]
            generic_exact_token_matches = [
                token
                for token in exact_token_matches
                if token in MISSING_STORAGE_GENERIC_TOKENS
            ]
            partial_token_matches = self._missing_storage_partial_token_matches(
                dataset_tokens,
                access_tokens,
            )
            strong_partial_token_matches = [
                match
                for match in partial_token_matches
                if not self._missing_storage_partial_match_is_generic(match)
            ]
            generic_partial_token_matches = [
                match
                for match in partial_token_matches
                if self._missing_storage_partial_match_is_generic(match)
            ]
            if strong_exact_token_matches:
                match_reasons.append("dataset_token_overlap")
                score += 12 * len(strong_exact_token_matches)
            if generic_exact_token_matches:
                match_reasons.append("generic_dataset_token_overlap")
                score += len(generic_exact_token_matches)
            if strong_partial_token_matches:
                match_reasons.append("dataset_token_partial_overlap")
                score += 6 * len(strong_partial_token_matches)
            if generic_partial_token_matches:
                match_reasons.append("generic_dataset_token_partial_overlap")
                score += len(generic_partial_token_matches)
            linked_dataset_iris = [
                iri
                for iri in self._subjects(
                    data_graphs,
                    "rc:hasStorageAccess",
                    access.iri,
                )
                if iri != dataset.iri
            ]
            if linked_dataset_iris:
                match_reasons.append("linked_to_other_dataset")
            if (
                linked_dataset_iris
                and "shares_dataset_path_template" not in match_reasons
            ):
                score -= 15
            route_role_labels = [
                role.label or self._local_name(role.iri)
                for role in access.route_roles
            ]
            candidate = {
                "storage_access": to_jsonable(self._summary_from_description(access)),
                "storage_access_iri": access.iri,
                "route_roles": to_jsonable(access.route_roles),
                "route_role_labels": route_role_labels,
                "storage_protocol": to_jsonable(access.storage_protocol),
                "access_mode": to_jsonable(access.access_mode),
                "location_kind": access.location_kind,
                "storage_root": access.storage_root,
                "endpoint_profile": access.endpoint_profile,
                "bucket_name": access.bucket_name,
                "key_prefix": access.key_prefix,
                "region": access.region,
                "credential_reference": access.credential_reference,
                "path_style_access": access.path_style_access,
                "path_templates": access.path_templates,
                "layout_verification_status": to_jsonable(
                    access.layout_verification_status
                ),
                "layout_verification_note": access.layout_verification_note,
                "match_reasons": match_reasons,
                "dataset_token_matches": strong_exact_token_matches,
                "generic_dataset_token_matches": generic_exact_token_matches,
                "dataset_partial_token_matches": strong_partial_token_matches,
                "generic_dataset_partial_token_matches": (
                    generic_partial_token_matches
                ),
                "linked_dataset_iris": linked_dataset_iris,
                "review_note": (
                    "Candidate existing storage access found in the current map. "
                    "Link it only after reviewing that its protocol, location, "
                    "path/relation templates, and access mode fit this dataset."
                ),
            }
            pending_staged_repair_iris = pending_staged_links.get(access.iri, [])
            if pending_staged_repair_iris:
                candidate["candidate_status"] = "already_pending"
                candidate["pending_staged_repair_iris"] = pending_staged_repair_iris
                candidate["review_note"] = (
                    "A current staged repair already proposes linking this "
                    "storage access to the dataset. Review that staged work "
                    "before staging a duplicate rc:hasStorageAccess link."
                )
            candidates.append((-score, label, access.iri, candidate))

        sorted_candidates = sorted(candidates)
        selected_candidates: list[dict[str, Any]] = []
        for rank, (_score, _label, _iri, candidate) in enumerate(
            sorted_candidates[:limit],
            start=1,
        ):
            ranked_candidate = dict(candidate)
            ranked_candidate["candidate_rank"] = rank
            selected_candidates.append(ranked_candidate)
        return selected_candidates, len(sorted_candidates)
    @staticmethod
    def _missing_storage_candidate_tokens(
        values: Iterable[str | None],
    ) -> set[str]:
        stopwords = {
            "a",
            "an",
            "and",
            "by",
            "connection",
            "directory",
            "for",
            "has",
            "is",
            "local",
            "of",
            "remote",
            "storage",
            "the",
        }
        tokens: set[str] = set()
        for value in values:
            if not value:
                continue
            spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(value))
            for token in re.findall(r"[A-Za-z0-9]+", spaced):
                lowered = token.lower()
                if lowered not in stopwords:
                    tokens.add(lowered)
        return tokens
    @staticmethod
    def _missing_storage_partial_match_is_generic(match: str) -> bool:
        parts = match.split(":", 1)
        return any(part in MISSING_STORAGE_GENERIC_TOKENS for part in parts)
    def _query_layout_signature_compatible_with_candidate(
        self,
        candidate: QueryTargetCandidate,
        file_format_iri: str | None,
    ) -> bool:
        layout_route_kind = self._query_file_format_layout_route_kind(file_format_iri)
        if layout_route_kind is None:
            return True
        return layout_route_kind == self._query_candidate_layout_route_kind(candidate)
    def _query_candidate_layout_route_kind(
        self,
        candidate: QueryTargetCandidate,
    ) -> TypingLiteral["database", "file"]:
        if self._is_database_storage(candidate.storage_protocol):
            return "database"
        return "file"
    def _sort_query_planning_issues(
        self,
        issues: Iterable[QueryPlanningIssue],
    ) -> list[QueryPlanningIssue]:
        deduped: list[QueryPlanningIssue] = []
        seen: set[tuple[str, str, str, str | None]] = set()
        for issue in issues:
            key = (
                issue.code,
                issue.severity,
                issue.message,
                issue.resource.iri if issue.resource is not None else None,
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(issue)
        severity_rank = {"error": 0, "warning": 1, "info": 2}
        return sorted(
            deduped,
            key=lambda issue: (
                severity_rank.get(issue.severity, 3),
                issue.code,
                issue.resource.iri if issue.resource is not None else "",
                issue.message,
            ),
        )
    def _query_planning_readiness(
        self,
        issues: list[QueryPlanningIssue],
    ) -> str:
        if any(issue.code == "contradicted_layout" for issue in issues):
            return "blocked_by_contradiction"
        if any(issue.severity == "error" for issue in issues):
            return "insufficient_metadata"
        if any(issue.severity == "warning" for issue in issues):
            return "needs_review"
        return "ready_for_query_planning"
    def _summary_from_description(self, description: Any) -> ResourceSummary:
        return ResourceSummary(
            iri=description.iri,
            label=description.label or self._local_name(description.iri),
            description=description.description,
        )
    @staticmethod
    def _graph_triple_object_matches_assertion_candidate(
        triple: GraphTripleDescription,
        *,
        object_value: str,
        object_kind: str,
        object_datatype: str | None,
        object_lang: str | None,
    ) -> bool:
        normalized_kind = "uri" if object_kind == "iri" else object_kind
        return (
            triple.object == object_value
            and triple.object_kind == normalized_kind
            and triple.datatype == object_datatype
            and triple.lang == object_lang
        )
    @staticmethod
    def _query_planning_issue_code_from_review_note(
        review_note: str,
    ) -> str | None:
        match = re.search(
            r"Generated from ([A-Za-z0-9_:-]+) query planning guidance",
            review_note,
        )
        if match is None:
            return None
        return match.group(1)
    def _local_name(self, iri: str) -> str | None:
        if "#" in iri:
            return iri.rsplit("#", 1)[1]
        if "/" in iri:
            return iri.rstrip("/").rsplit("/", 1)[1]
        return None
