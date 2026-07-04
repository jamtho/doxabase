"""Query result/evidence recording and storage overlays.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via QueryEvidenceMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class QueryEvidenceMixin:
    def _query_context_ordinary_query_evidence_actions(
        self,
        dataset: DatasetDescription,
        profile_summary: ProfileSummary,
        *,
        issues: list[QueryPlanningIssue],
        exclude_evidence_iris: set[str] | None = None,
    ) -> list[SuggestedNextAction]:
        if not self._query_context_should_suggest_evidence_storage_overlay(
            issues
        ):
            return []
        evidence_iris = self._query_context_dataset_query_evidence_iris(
            dataset.iri,
            exclude_evidence_iris=exclude_evidence_iris or set(),
        )
        actions: list[SuggestedNextAction] = []
        for evidence_iri in evidence_iris[:3]:
            evidence = self._describe_evidence(
                evidence_iri,
                self._expand_graphs(["evidence"]),
                self._lookup_graphs(self._expand_graphs(["all"])),
            )
            source_query_evidence = self._query_context_source_profile_evidence(
                evidence_iri,
                [],
                evidence=evidence,
            )
            actions.append(
                self._query_context_evidence_storage_overlay_action(
                    dataset_iri=dataset.iri,
                    evidence_iri=evidence_iri,
                    source_profile_evidence=source_query_evidence,
                )
            )
        return actions
    def _query_context_dataset_query_evidence_iris(
        self,
        dataset_iri: str,
        *,
        exclude_evidence_iris: set[str],
    ) -> list[str]:
        observation_graphs = self._expand_graphs(["observations"])
        evidence_graphs = self._expand_graphs(["evidence"])
        rows: list[tuple[str, str, str]] = []
        for observation_iri in self._subjects(
            observation_graphs,
            "rc:observedAsset",
            dataset_iri,
        ):
            observed_at = self._first_object(
                observation_graphs,
                observation_iri,
                "rc:observedAt",
            ) or ""
            for evidence_iri in self._objects(
                observation_graphs,
                observation_iri,
                "rc:evidence",
            ):
                if evidence_iri in exclude_evidence_iris:
                    continue
                if (
                    self._first_object(
                        evidence_graphs,
                        evidence_iri,
                        "rc:queryExecutionStatus",
                    )
                    is None
                ):
                    continue
                rows.append((observed_at, observation_iri, evidence_iri))
        rows.sort(reverse=True)
        return list(dict.fromkeys(evidence_iri for _, _, evidence_iri in rows))
    @staticmethod
    def _query_context_should_suggest_evidence_storage_overlay(
        issues: Iterable[QueryPlanningIssue],
    ) -> bool:
        overlay_issue_codes = {
            "missing_storage_access",
            "missing_path_template",
            "missing_physical_layout",
            "missing_file_format",
            "missing_storage_protocol",
            "missing_storage_location",
            "layout_needs_verification",
        }
        return any(issue.code in overlay_issue_codes for issue in issues)
    def _query_context_evidence_storage_overlay_action(
        self,
        *,
        dataset_iri: str,
        evidence_iri: str,
        source_profile_evidence: dict[str, Any],
    ) -> QueryEvidenceOverlaySuggestedNextAction:
        (
            evidence_storage_route_candidates,
            evidence_storage_route_candidate_total,
        ) = self._query_context_evidence_storage_route_candidates_for_evidence(
            evidence_iri,
            limit=6,
        )
        arguments = {
            "dataset_iri": dataset_iri,
            "evidence_iri": evidence_iri,
            "storage_protocol": "REVIEWED_STORAGE_PROTOCOL",
            "storage_root": "REVIEWED_STORAGE_ROOT_OR_URI",
            "endpoint_profile": "<optional reviewed endpoint profile>",
            "bucket_name": "<optional reviewed S3 bucket name>",
            "key_prefix": "<optional reviewed S3 key prefix>",
            "region": "<optional reviewed S3 region>",
            "path_style_access": "<optional reviewed boolean>",
            "credential_reference": "<optional non-secret credential reference>",
            "location_kind": "REVIEWED_LOCATION_KIND",
            "path_templates": ["REVIEWED_PATH_TEMPLATE"],
            "file_format": "REVIEWED_FILE_FORMAT",
            "layout_verification_note": "REVIEWED_LAYOUT_VERIFICATION_NOTE",
        }
        required = [
            "storage_protocol",
            "storage_root",
            "location_kind",
            "file_format",
        ]
        placeholders = [
            "storage_protocol",
            "storage_root",
            "endpoint_profile",
            "bucket_name",
            "key_prefix",
            "region",
            "path_style_access",
            "credential_reference",
            "location_kind",
            "path_templates",
            "file_format",
            "layout_verification_note",
        ]
        return QueryEvidenceOverlaySuggestedNextAction(
            action_label="Draft query evidence storage overlay",
            tool_name="draft_query_evidence_storage_overlay",
            mcp_tool_name="doxabase.draft_query_evidence_storage_overlay",
            arguments=arguments,
            reason=(
                "This query context has singleton query/profile evidence and "
                "physical metadata blockers. Review the evidence, replace the "
                "storage/path/layout placeholders with confirmed non-secret "
                "values, then draft a storage overlay instead of hand-authoring "
                "RDF."
            ),
            call=self._suggested_call_string(
                "draft_query_evidence_storage_overlay",
                arguments,
            ),
            source_profile_evidence=source_profile_evidence,
            source_query_evidence=source_profile_evidence,
            evidence_storage_route_candidates=evidence_storage_route_candidates,
            evidence_storage_route_candidate_count=len(
                evidence_storage_route_candidates
            ),
            evidence_storage_route_candidate_total_count=(
                evidence_storage_route_candidate_total
            ),
            evidence_storage_route_candidates_truncated=(
                evidence_storage_route_candidate_total
                > len(evidence_storage_route_candidates)
            ),
            required_extra_arguments=required,
            placeholder_fields=placeholders,
            reviewed_value_fields=placeholders,
            template_note=(
                "Placeholders are not automatically applied from query artifacts. "
                "Use evidence_storage_route_candidates as review-only drafts "
                "when present, then replace placeholders with reviewed storage, "
                "path, and layout values before calling the helper."
            ),
        )
    def _query_evidence_linked_to_dataset(
        self,
        *,
        dataset_iri: str,
        evidence_iri: str,
    ) -> bool:
        observation_graphs = self._expand_graphs(["observations"])
        for observation_iri in self._subjects(
            observation_graphs,
            "rc:evidence",
            evidence_iri,
        ):
            if dataset_iri in self._objects(
                observation_graphs,
                observation_iri,
                "rc:observedAsset",
            ):
                return True
        return False
    @classmethod
    def _query_result_metadata_from_evidence(
        cls,
        evidence: EvidenceDescription | None,
    ) -> dict[str, str | None]:
        metadata = cls._query_result_metadata_from_evidence_summary(
            evidence.summary if evidence is not None else None
        )
        if evidence is None:
            return metadata
        return {
            "execution_status": evidence.query_execution_status
            or metadata["execution_status"],
            "engine": evidence.query_engine or metadata["engine"],
            "query_hash": evidence.query_hash or metadata["query_hash"],
        }
    @staticmethod
    def _query_result_metadata_from_evidence_summary(
        evidence_summary: str | None,
    ) -> dict[str, str | None]:
        metadata: dict[str, str | None] = {
            "execution_status": None,
            "engine": None,
            "query_hash": None,
        }
        if not evidence_summary:
            return metadata
        status_match = re.search(
            r"(?:^|\s)External query execution ([^.]+)\.",
            evidence_summary,
        )
        if status_match:
            metadata["execution_status"] = status_match.group(1).strip()
        engine_match = re.search(r"(?:^|\s)Engine: ([^.]+)\.", evidence_summary)
        if engine_match:
            metadata["engine"] = engine_match.group(1).strip()
        hash_match = re.search(r"(?:^|\s)Query hash: ([^.]+)\.", evidence_summary)
        if hash_match:
            metadata["query_hash"] = hash_match.group(1).strip()
        return metadata
    def draft_query_evidence_storage_overlay(
        self,
        dataset_iri: str,
        evidence_iri: str,
        *,
        storage_protocol: str,
        storage_root: str,
        location_kind: str,
        file_format: str,
        graph: str | None = "map",
        storage_access_iri: str | None = None,
        physical_layout_iri: str | None = None,
        storage_label: str | None = None,
        physical_layout_label: str | None = None,
        route_roles: Iterable[str] | str | None = None,
        access_mode: str | None = "rc:ReadOnlyAccess",
        endpoint_profile: str | None = None,
        bucket_name: str | None = None,
        key_prefix: str | None = None,
        region: str | None = None,
        path_style_access: bool | None = None,
        credential_reference: str | None = None,
        path_templates: Iterable[str] | str | None = None,
        compression_codec: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
    ) -> QueryEvidenceStorageOverlayDraft | QueryEvidenceStorageOverlayBlocker:
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        evidence_value = self._required_iri("evidence_iri", evidence_iri)
        storage_root_value = storage_root.strip()
        if not storage_root_value:
            raise DoxaBaseError("storage_root must not be empty")
        location_kind_value = self._storage_location_kind(location_kind)
        if location_kind_value is None:
            raise DoxaBaseError("location_kind must not be empty")
        storage_protocol_ref = self._resource_ref(
            "storage_protocol",
            storage_protocol,
        )
        file_format_ref = self._resource_ref("file_format", file_format)
        access_mode_ref = (
            self._resource_ref("access_mode", access_mode)
            if access_mode is not None
            else None
        )
        compression_codec_ref = (
            self._resource_ref("compression_codec", compression_codec)
            if compression_codec is not None
            else None
        )

        profile_run = self.describe_profile_run(
            dataset_value,
            evidence_value,
            graph=graph,
            limit=None,
        )
        all_profiles = [
            *profile_run.dataset_profile_observations,
            *profile_run.mapped_column_profile_observations,
            *profile_run.unmapped_column_profile_observations,
        ]
        source_query_evidence = self._query_context_source_profile_evidence(
            evidence_value,
            all_profiles,
            evidence=profile_run.evidence,
        )
        (
            evidence_storage_route_candidates,
            evidence_storage_route_candidate_total,
        ) = self._query_context_evidence_storage_route_candidates_for_evidence(
            evidence_value,
            limit=6,
            evidence=profile_run.evidence,
        )
        if (
            profile_run.total_profile_count == 0
            and not source_query_evidence.get("execution_status")
        ):
            raise DoxaBaseError(
                "draft_query_evidence_storage_overlay requires profile or "
                "query-result evidence linked to the dataset"
            )
        if (
            profile_run.total_profile_count == 0
            and not self._query_evidence_linked_to_dataset(
                dataset_iri=dataset_value,
                evidence_iri=evidence_value,
            )
        ):
            raise DoxaBaseError(
                "draft_query_evidence_storage_overlay requires query-result "
                "evidence linked to the requested dataset when no profile "
                "observations use the evidence"
            )
        source_query_context = self.describe_query_context(dataset_value, graph=graph)
        source_profile_evidence = source_query_evidence
        execution_status = source_query_evidence.get("execution_status")
        effective_layout_status = layout_verification_status or (
            "rc:VerifiedByQueryLayout"
            if execution_status == "succeeded"
            else "rc:CandidateLayout"
        )
        layout_verification_status_ref = self._controlled_resource_ref(
            "layout_verification_status",
            effective_layout_status,
            LAYOUT_VERIFICATION_STATUSES,
        )

        route_role_values = self._string_values("route_roles", route_roles)
        path_template_values = self._string_values(
            "path_templates",
            path_templates,
        )
        storage_access_value = (
            self._required_iri("storage_access_iri", storage_access_iri)
            if storage_access_iri is not None
            else self._query_evidence_overlay_generated_iri(
                "storage-access",
                dataset_value,
                evidence_value,
                storage_root_value,
                path_template_values,
            )
        )
        physical_layout_value = (
            self._required_iri("physical_layout_iri", physical_layout_iri)
            if physical_layout_iri is not None
            else self._query_evidence_overlay_generated_iri(
                "physical-layout",
                dataset_value,
                evidence_value,
                str(file_format_ref),
                compression_codec,
            )
        )

        graph_payload = self._query_evidence_storage_overlay_graph(
            dataset_iri=dataset_value,
            storage_access_iri=storage_access_value,
            physical_layout_iri=physical_layout_value,
            storage_label=storage_label,
            physical_layout_label=physical_layout_label,
            route_roles=route_role_values,
            storage_protocol=storage_protocol_ref,
            access_mode=access_mode_ref,
            location_kind=location_kind_value,
            storage_root=storage_root_value,
            endpoint_profile=endpoint_profile,
            bucket_name=bucket_name,
            key_prefix=key_prefix,
            region=region,
            path_style_access=path_style_access,
            credential_reference=credential_reference,
            path_templates=path_template_values,
            file_format=file_format_ref,
            compression_codec=compression_codec_ref,
            layout_verification_status=layout_verification_status_ref,
            layout_verification_note=layout_verification_note,
        )
        stale_seed_blocker = (
            self._query_evidence_storage_overlay_stale_seed_blocker(
                dataset=profile_run.dataset,
                evidence=profile_run.evidence,
                evidence_iri=evidence_value,
                source_query_context=source_query_context,
                source_profile_evidence=source_profile_evidence,
                source_query_evidence=source_query_evidence,
                evidence_storage_route_candidates=evidence_storage_route_candidates,
                evidence_storage_route_candidate_total=(
                    evidence_storage_route_candidate_total
                ),
            )
        )
        if stale_seed_blocker is not None:
            return stale_seed_blocker
        removals = self._query_evidence_storage_overlay_removals(
            dataset_iri=dataset_value,
            storage_access_iri=storage_access_value,
            physical_layout_iri=physical_layout_value,
            layout_verification_status=layout_verification_status_ref,
            layout_verification_note=layout_verification_note,
        )
        content = graph_payload.serialize(format="turtle")
        additions = [{"graph": "map", "format": "turtle", "content": content}]
        parsed_patches = self._parse_staged_patch_specs(
            additions=additions,
            removals=removals,
        )
        preview = self._preview_staged_graph_patches(
            parsed_patches,
            validation_scope=validation_scope,
            revision_has_support_metadata=True,
        )

        dataset_label = profile_run.dataset.label or self._local_name(dataset_value)
        summary = f"Stage query evidence storage overlay for {dataset_label or dataset_value}"
        review_note = (
            "Generated by draft_query_evidence_storage_overlay from reviewed "
            "query/profile evidence. The helper did not infer storage paths from "
            "artifacts; the caller supplied reviewed storage, path, and layout "
            "values."
        )
        review_recommendation = (
            "Apply only after confirming the storage root/templates describe the "
            "queried source data rather than query text, logs, or result output."
        )
        rationale = (
            "Profile/query evidence "
            f"{evidence_value} supports adding reviewed storage access and "
            "physical layout metadata so query planning can draft a physical "
            "handoff without hand-authored RDF."
        )
        stage_arguments: dict[str, Any] = {
            "summary": summary,
            "rationale": rationale,
            "additions": additions,
            "supporting_observations": list(profile_run.profile_observation_iris),
            "evidence": [evidence_value],
            "revision_anchors": [
                dataset_value,
                storage_access_value,
                physical_layout_value,
            ],
            "included_graphs": ["map", "observations", "evidence"],
            "review_note": review_note,
            "review_recommendation": review_recommendation,
            "validation_scope": validation_scope,
        }
        if removals:
            stage_arguments["removals"] = removals
        stage_action = SuggestedNextAction(
            action_label="Stage query evidence storage overlay",
            tool_name="stage_graph_revision",
            mcp_tool_name="doxabase.stage_graph_revision",
            arguments=stage_arguments,
            reason=(
                "Stage the reviewed storage/path/layout overlay as a graph "
                "revision before applying it to current map facts."
            ),
            call=self._suggested_call_string(
                "stage_graph_revision",
                stage_arguments,
            ),
        )
        dataset_replaced_layout_values = (
            self._query_evidence_overlay_replaced_layout_verification_values(
                dataset_value,
                layout_verification_status=layout_verification_status_ref,
                layout_verification_note=layout_verification_note,
            )
        )
        storage_replaced_layout_values = (
            self._query_evidence_overlay_replaced_layout_verification_values(
                storage_access_value,
                layout_verification_status=layout_verification_status_ref,
                layout_verification_note=layout_verification_note,
            )
        )
        physical_layout_replaced_layout_values = (
            self._query_evidence_overlay_replaced_layout_verification_values(
                physical_layout_value,
                layout_verification_status=layout_verification_status_ref,
                layout_verification_note=layout_verification_note,
            )
        )
        reviewed_overlay = {
            "storage_access_iri": storage_access_value,
            "physical_layout_iri": physical_layout_value,
            "storage_label": storage_label,
            "physical_layout_label": physical_layout_label,
            "route_roles": [
                self.expand_iri(route_role) for route_role in route_role_values
            ],
            "storage_protocol": str(storage_protocol_ref),
            "storage_root": storage_root_value,
            "access_mode": str(access_mode_ref) if access_mode_ref is not None else None,
            "location_kind": location_kind_value,
            "endpoint_profile": endpoint_profile,
            "bucket_name": bucket_name,
            "key_prefix": key_prefix,
            "region": region,
            "path_style_access": path_style_access,
            "credential_reference": credential_reference,
            "path_templates": path_template_values,
            "file_format": str(file_format_ref),
            "compression_codec": (
                str(compression_codec_ref)
                if compression_codec_ref is not None
                else None
            ),
            "layout_verification_status": str(layout_verification_status_ref),
            "layout_verification_note": layout_verification_note,
            "replaced_dataset_layout_verification_statuses": (
                dataset_replaced_layout_values["layout_verification_statuses"]
            ),
            "replaced_dataset_layout_verification_notes": (
                dataset_replaced_layout_values["layout_verification_notes"]
            ),
            "replaced_storage_access_layout_verification_statuses": (
                storage_replaced_layout_values["layout_verification_statuses"]
            ),
            "replaced_storage_access_layout_verification_notes": (
                storage_replaced_layout_values["layout_verification_notes"]
            ),
            "replaced_physical_layout_verification_statuses": (
                physical_layout_replaced_layout_values[
                    "layout_verification_statuses"
                ]
            ),
            "replaced_physical_layout_verification_notes": (
                physical_layout_replaced_layout_values[
                    "layout_verification_notes"
                ]
            ),
        }
        return QueryEvidenceStorageOverlayDraft(
            result_kind="query_evidence_storage_overlay_draft",
            helper="draft_query_evidence_storage_overlay",
            mode="non_mutating_stage_arguments",
            dataset=profile_run.dataset,
            evidence=profile_run.evidence,
            evidence_iri=evidence_value,
            source_query_context_readiness=source_query_context.readiness,
            source_query_context_issue_codes=self._query_issue_codes(
                source_query_context.issues
            ),
            source_profile_evidence=source_profile_evidence,
            source_query_evidence=source_query_evidence,
            evidence_storage_route_candidates=evidence_storage_route_candidates,
            evidence_storage_route_candidate_count=len(
                evidence_storage_route_candidates
            ),
            evidence_storage_route_candidate_total_count=(
                evidence_storage_route_candidate_total
            ),
            evidence_storage_route_candidates_truncated=(
                evidence_storage_route_candidate_total
                > len(evidence_storage_route_candidates)
            ),
            profile_observation_iris=list(profile_run.profile_observation_iris),
            storage_access_iri=storage_access_value,
            physical_layout_iri=physical_layout_value,
            reviewed_overlay=reviewed_overlay,
            additions=additions,
            changed_graphs=preview.changed_graphs,
            patches=preview.patch_descriptions,
            validation_scope=preview.validation.scope,
            validation_conforms=preview.validation.conforms,
            validation_result_count=preview.validation.result_count,
            validation_results=preview.validation.results,
            validation_report_text=preview.validation.report_text,
            review_note=review_note,
            review_recommendation=review_recommendation,
            stage_arguments=stage_arguments,
            suggested_next_actions=[stage_action],
            suggested_next_calls=[stage_action.call],
        )
    def _query_evidence_storage_overlay_stale_seed_blocker(
        self,
        *,
        dataset: ResourceSummary,
        evidence: EvidenceDescription,
        evidence_iri: str,
        source_query_context: QueryPlanningContext,
        source_profile_evidence: dict[str, Any],
        source_query_evidence: dict[str, Any],
        evidence_storage_route_candidates: list[dict[str, Any]],
        evidence_storage_route_candidate_total: int,
    ) -> QueryEvidenceStorageOverlayBlocker | None:
        missing_seed_terms = self._missing_base_ontology_terms(
            REQUIRED_STAGING_ONTOLOGY_TERMS,
        )
        if not missing_seed_terms:
            return None
        arguments = self._stale_seed_handoff_preflight_arguments()
        action = SuggestedNextAction(
            action_label="Preflight stale seed project handoff export",
            tool_name="export_preflight",
            mcp_tool_name="doxabase.export_preflight",
            arguments=arguments,
            reason=(
                "The immutable base_ontology is missing current staging seed "
                "terms, so this overlay cannot safely produce stage arguments "
                "in the current capsule. Preflight a project/history handoff "
                "with map validation before recovering into a fresh seeded "
                "capsule."
            ),
            call=self._suggested_call_string("export_preflight", arguments),
        )
        return QueryEvidenceStorageOverlayBlocker(
            result_kind="query_evidence_storage_overlay_blocker",
            helper="draft_query_evidence_storage_overlay",
            mode="blocked_stale_seed_recovery_required",
            dataset=dataset,
            evidence=evidence,
            evidence_iri=evidence_iri,
            source_query_context_readiness=source_query_context.readiness,
            source_query_context_issue_codes=self._query_issue_codes(
                source_query_context.issues
            ),
            source_profile_evidence=source_profile_evidence,
            source_query_evidence=source_query_evidence,
            evidence_storage_route_candidates=evidence_storage_route_candidates,
            evidence_storage_route_candidate_count=len(
                evidence_storage_route_candidates
            ),
            evidence_storage_route_candidate_total_count=(
                evidence_storage_route_candidate_total
            ),
            evidence_storage_route_candidates_truncated=(
                evidence_storage_route_candidate_total
                > len(evidence_storage_route_candidates)
            ),
            missing_seed_terms=missing_seed_terms,
            mutation_allowed_after="stale_seed_recovery_required_before_staging",
            note=self._stale_seed_recovery_message(missing_seed_terms),
            suggested_next_actions=[action],
            suggested_next_calls=[action.call],
        )
    def _query_evidence_storage_overlay_graph(
        self,
        *,
        dataset_iri: str,
        storage_access_iri: str,
        physical_layout_iri: str,
        storage_label: str | None,
        physical_layout_label: str | None,
        route_roles: list[str],
        storage_protocol: URIRef,
        access_mode: URIRef | None,
        location_kind: str,
        storage_root: str,
        endpoint_profile: str | None,
        bucket_name: str | None,
        key_prefix: str | None,
        region: str | None,
        path_style_access: bool | None,
        credential_reference: str | None,
        path_templates: list[str],
        file_format: URIRef,
        compression_codec: URIRef | None,
        layout_verification_status: URIRef,
        layout_verification_note: str | None,
    ) -> Graph:
        graph = Graph()
        self._bind_prefixes(graph)
        dataset = URIRef(dataset_iri)
        storage = URIRef(storage_access_iri)
        layout = URIRef(physical_layout_iri)
        graph.add((dataset, URIRef(self.expand_iri("rc:hasStorageAccess")), storage))
        graph.add((dataset, URIRef(self.expand_iri("rc:hasPhysicalLayout")), layout))
        graph.add(
            (
                dataset,
                URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                layout_verification_status,
            )
        )
        self._add_optional_literal(
            graph,
            dataset,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )

        graph.add((storage, RDF.type, URIRef(self.expand_iri("rc:StorageAccess"))))
        self._add_optional_literal(graph, storage, str(RDFS.label), storage_label)
        for route_role in route_roles:
            graph.add(
                (
                    storage,
                    URIRef(self.expand_iri("rc:routeRole")),
                    self._resource_ref("route_roles", route_role),
                )
            )
        graph.add(
            (
                storage,
                URIRef(self.expand_iri("rc:storageProtocol")),
                storage_protocol,
            )
        )
        if access_mode is not None:
            graph.add(
                (storage, URIRef(self.expand_iri("rc:accessMode")), access_mode)
            )
        for predicate, value in (
            ("rc:locationKind", location_kind),
            ("rc:storageRoot", storage_root),
            ("rc:endpointProfile", endpoint_profile),
            ("rc:bucketName", bucket_name),
            ("rc:keyPrefix", key_prefix),
            ("rc:region", region),
            ("rc:credentialReference", credential_reference),
        ):
            self._add_optional_literal(graph, storage, predicate, value)
        if path_style_access is not None:
            graph.add(
                (
                    storage,
                    URIRef(self.expand_iri("rc:pathStyleAccess")),
                    Literal(path_style_access, datatype=XSD.boolean),
                )
            )
        for path_template in path_templates:
            graph.add(
                (
                    storage,
                    URIRef(self.expand_iri("rc:pathTemplate")),
                    Literal(path_template),
                )
            )
        graph.add(
            (
                storage,
                URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                layout_verification_status,
            )
        )
        self._add_optional_literal(
            graph,
            storage,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )

        graph.add((layout, RDF.type, URIRef(self.expand_iri("rc:PhysicalLayout"))))
        self._add_optional_literal(
            graph,
            layout,
            str(RDFS.label),
            physical_layout_label,
        )
        graph.add((layout, URIRef(self.expand_iri("rc:fileFormat")), file_format))
        if compression_codec is not None:
            graph.add(
                (
                    layout,
                    URIRef(self.expand_iri("rc:compressionCodec")),
                    compression_codec,
                )
            )
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
    def _query_evidence_storage_overlay_removals(
        self,
        *,
        dataset_iri: str,
        storage_access_iri: str,
        physical_layout_iri: str,
        layout_verification_status: URIRef,
        layout_verification_note: str | None,
    ) -> list[dict[str, str]] | None:
        removal_graph = Graph()
        self._bind_prefixes(removal_graph)
        status_predicate = URIRef(self.expand_iri("rc:layoutVerificationStatus"))
        note_predicate = URIRef(self.expand_iri("rc:layoutVerificationNote"))
        for subject_iri in (
            dataset_iri,
            storage_access_iri,
            physical_layout_iri,
        ):
            subject = URIRef(subject_iri)
            replaced_values = (
                self._query_evidence_overlay_replaced_layout_verification_values(
                    subject_iri,
                    layout_verification_status=layout_verification_status,
                    layout_verification_note=layout_verification_note,
                )
            )
            for existing_status in replaced_values["layout_verification_statuses"]:
                removal_graph.add(
                    (
                        subject,
                        status_predicate,
                        URIRef(existing_status),
                    )
                )
            for existing_note in replaced_values["layout_verification_notes"]:
                removal_graph.add((subject, note_predicate, Literal(existing_note)))
        if len(removal_graph) == 0:
            return None
        return [
            {
                "graph": "map",
                "format": "turtle",
                "content": removal_graph.serialize(format="turtle"),
            }
        ]
    def _query_evidence_overlay_replaced_layout_verification_values(
        self,
        subject_iri: str,
        *,
        layout_verification_status: URIRef,
        layout_verification_note: str | None,
    ) -> dict[str, list[str]]:
        return {
            "layout_verification_statuses": (
                self._query_evidence_overlay_existing_values_replaced(
                    subject_iri,
                    "rc:layoutVerificationStatus",
                    str(layout_verification_status),
                )
            ),
            "layout_verification_notes": (
                self._query_evidence_overlay_existing_values_replaced(
                    subject_iri,
                    "rc:layoutVerificationNote",
                    layout_verification_note,
                )
                if layout_verification_note is not None
                else []
            ),
        }
    def _query_evidence_overlay_existing_values_replaced(
        self,
        subject_iri: str,
        predicate: str,
        replacement_value: str | None,
    ) -> list[str]:
        if replacement_value is None:
            return []
        return [
            value
            for value in self._objects(["map"], subject_iri, predicate)
            if value != replacement_value
        ]
    @staticmethod
    def _query_evidence_overlay_generated_iri(
        kind: str,
        *values: Any,
    ) -> str:
        payload = json.dumps(values, sort_keys=True, default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return f"https://richcanopy.org/doxabase/generated/{kind}/{digest}"
    def record_query_result(
        self,
        summary: str,
        *,
        observed_asset: str | None = None,
        observed_at: datetime | str | None = None,
        observed_by: str | None = None,
        execution_status: str = "succeeded",
        engine: str | None = None,
        query_source_path: str | None = None,
        query_source_section: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        query_hash: str | None = None,
        result_sources: Iterable[str] | str | None = None,
        scanned_source_paths: Iterable[str] | str | None = None,
        scanned_source_handles: Iterable[str] | str | None = None,
        evidence_summary: str | None = None,
        failure_summary: str | None = None,
        sample_size: int | None = None,
        sample_scope: str | None = None,
        sample_method: str | None = None,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
        value_frequencies: Iterable[Mapping[str, Any]] | None = None,
        profile_metrics: Iterable[Mapping[str, Any]] | None = None,
        observation_iri: str | None = None,
        evidence_iri: str | None = None,
        source_span_iri: str | None = None,
    ) -> QueryResultRecord:
        """Record an externally executed query result or failure as evidence."""
        status_value = self._query_execution_status(execution_status)
        engine_value = engine.strip() if engine and engine.strip() else None
        query_source_path_value = (
            query_source_path.strip()
            if query_source_path and query_source_path.strip()
            else None
        )
        query_source_section_value = (
            query_source_section.strip()
            if query_source_section and query_source_section.strip()
            else None
        )
        query_hash_value = (
            query_hash.strip() if query_hash and query_hash.strip() else None
        )
        failure_summary_value = (
            failure_summary.strip()
            if failure_summary and failure_summary.strip()
            else None
        )
        result_source_values = self._string_values("result_sources", result_sources)
        scanned_source_path_values = self._string_values(
            "scanned_source_paths",
            scanned_source_paths,
        )
        scanned_source_handle_values = list(
            dict.fromkeys(
                [
                    *scanned_source_path_values,
                    *self._string_values(
                        "scanned_source_handles",
                        scanned_source_handles,
                    ),
                ]
            )
        )
        if (
            not result_source_values
            and query_source_path_value is None
            and not scanned_source_handle_values
        ):
            raise DoxaBaseError(
                "record_query_result requires result_sources, query_source_path, "
                "scanned_source_paths, or scanned_source_handles"
            )
        for name, value in {"start_line": start_line, "end_line": end_line}.items():
            if value is not None and value < 1:
                raise DoxaBaseError(f"{name} must be a positive one-based line number")
        profile_payload_present = any(
            value is not None
            for value in (
                sample_size,
                row_count,
                null_count,
                distinct_count,
                value_frequencies,
                profile_metrics,
            )
        )
        if status_value != "succeeded" and profile_payload_present:
            raise DoxaBaseError(
                "profile result fields require execution_status='succeeded'"
            )
        if query_source_path_value is not None:
            self._preflight_source_span_reuse(
                source_span_iri=source_span_iri,
                source_path=query_source_path_value,
                source_section=query_source_section_value,
                start_line=start_line,
                end_line=end_line,
                source_kind="rc:QuerySource",
            )
        observation_type: TypingLiteral["observation", "profile"] = (
            "profile" if profile_payload_present else "observation"
        )
        evidence_summary_value = evidence_summary
        if evidence_summary_value is None:
            evidence_summary_value = self._query_result_evidence_summary(
                status=status_value,
                engine=engine_value,
                query_hash=query_hash_value,
                failure_summary=failure_summary_value,
            )

        observation = self.record_observation(
            summary=summary,
            observation_type=observation_type,
            observed_asset=observed_asset,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary_value,
            evidence_sources=result_source_values,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method,
            row_count=row_count,
            null_count=null_count,
            distinct_count=distinct_count,
            value_frequencies=value_frequencies,
            profile_metrics=profile_metrics,
            observation_iri=observation_iri,
            evidence_iri=evidence_iri,
        )
        assert observation.evidence_iri is not None
        metadata_triples = self._insert_query_result_metadata(
            evidence_iri=observation.evidence_iri,
            execution_status=status_value,
            engine=engine_value,
            query_hash=query_hash_value,
            scanned_source_handles=scanned_source_handle_values,
        )
        source_span_triples = 0
        source_span_value: str | None = None
        scanned_source_span_values: list[str] = []
        if query_source_path_value is not None:
            span_iri, span_triples = self._insert_evidence_source_span(
                evidence_iri=observation.evidence_iri,
                source_path=query_source_path_value,
                source_section=query_source_section_value,
                start_line=start_line,
                end_line=end_line,
                source_kind="rc:QuerySource",
                source_span_iri=source_span_iri,
            )
            source_span_value = span_iri
            source_span_triples += span_triples
        for scanned_source_path in scanned_source_path_values:
            span_iri, span_triples = self._insert_evidence_source_span(
                evidence_iri=observation.evidence_iri,
                source_path=scanned_source_path,
                source_kind="rc:DataSampleSource",
            )
            scanned_source_span_values.append(span_iri)
            source_span_triples += span_triples

        suggested_next_actions = self._query_result_suggested_next_actions(
            observed_asset=observed_asset,
            observation_type=observation.observation_type,
            evidence_iri=observation.evidence_iri,
        )
        return QueryResultRecord(
            observation_iri=observation.observation_iri,
            observation_type=observation.observation_type,
            evidence_iri=observation.evidence_iri,
            source_span_iri=source_span_value,
            scanned_source_span_iris=scanned_source_span_values,
            execution_status=status_value,
            engine=engine_value,
            query_source_path=query_source_path_value,
            query_hash=query_hash_value,
            failure_summary=failure_summary_value,
            result_sources=result_source_values,
            scanned_source_paths=scanned_source_path_values,
            scanned_source_handles=scanned_source_handle_values,
            observation_triples=observation.observation_triples,
            evidence_triples=(
                observation.evidence_triples
                + metadata_triples
                + source_span_triples
            ),
            source_span_triples=source_span_triples,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions if action.call
            ],
        )
    def _query_result_suggested_next_actions(
        self,
        *,
        observed_asset: str | None,
        observation_type: str,
        evidence_iri: str,
    ) -> list[SuggestedNextAction]:
        if observed_asset is None:
            observed_asset_iri = None
        else:
            observed_asset_iri = self.expand_iri(observed_asset)
        actions: list[SuggestedNextAction] = []
        if observation_type == "profile" and observed_asset_iri is not None:
            profile_arguments = {
                "dataset_iri": observed_asset_iri,
                "evidence_iri": evidence_iri,
            }
            actions.append(
                SuggestedNextAction(
                    action_label="Inspect recorded profile result",
                    tool_name="describe_profile_run",
                    mcp_tool_name="doxabase.describe_profile_run",
                    arguments=profile_arguments,
                    reason=(
                        "This query result wrote profile-shaped evidence. "
                        "Inspect the profile run before promoting map facts or "
                        "relying on the result in a new query plan."
                    ),
                    call=self._suggested_call_string(
                        "describe_profile_run",
                        profile_arguments,
                    ),
                )
            )
        evidence_arguments = {
            "seed_iris": [evidence_iri],
            "profile": "resource_brief",
        }
        actions.append(
            SuggestedNextAction(
                action_label="Inspect recorded query evidence",
                tool_name="describe_context_slice",
                mcp_tool_name="doxabase.describe_context_slice",
                arguments=evidence_arguments,
                reason=(
                    "Inspect the evidence resource just written by "
                    "record_query_result, including query source spans, "
                    "scanned source handles, result sources, and execution "
                    "metadata before continuing query planning."
                ),
                call=self._suggested_call_string(
                    "describe_context_slice",
                    evidence_arguments,
                ),
            )
        )
        if observed_asset_iri is None:
            return actions
        context_arguments = {"iri": observed_asset_iri}
        actions.append(
            SuggestedNextAction(
                action_label="Refresh query context",
                tool_name="describe_query_context",
                mcp_tool_name="doxabase.describe_query_context",
                arguments=context_arguments,
                reason=(
                    "Refresh the dataset query context after recording this "
                    "external result so storage, profile, and next-plan routing "
                    "reflect the new evidence."
                ),
                call=self._suggested_call_string(
                    "describe_query_context",
                    context_arguments,
                ),
            )
        )
        return actions
    @staticmethod
    def _query_result_evidence_summary(
        *,
        status: str,
        engine: str | None,
        query_hash: str | None,
        failure_summary: str | None,
    ) -> str:
        parts = [f"External query execution {status}."]
        if engine is not None:
            parts.append(f"Engine: {engine}.")
        if query_hash is not None:
            parts.append(f"Query hash: {query_hash}.")
        if failure_summary is not None:
            parts.append(f"Failure summary: {failure_summary}")
        return " ".join(parts)
    def _insert_query_result_metadata(
        self,
        *,
        evidence_iri: str,
        execution_status: str,
        engine: str | None,
        query_hash: str | None,
        scanned_source_handles: list[str],
    ) -> int:
        evidence_graph = Graph()
        self._bind_prefixes(evidence_graph)
        evidence_subject = URIRef(evidence_iri)
        evidence_graph.add(
            (
                evidence_subject,
                URIRef(self.expand_iri("rc:queryExecutionStatus")),
                Literal(execution_status),
            )
        )
        self._add_optional_literal(
            evidence_graph,
            evidence_subject,
            "rc:queryEngine",
            engine,
        )
        self._add_optional_literal(
            evidence_graph,
            evidence_subject,
            "rc:queryHash",
            query_hash,
        )
        for handle in scanned_source_handles:
            evidence_graph.add(
                (
                    evidence_subject,
                    URIRef(self.expand_iri("rc:scannedSourceHandle")),
                    Literal(handle),
                )
            )
        return self._insert_graph("evidence", evidence_graph)
