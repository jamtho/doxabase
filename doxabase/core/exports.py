"""Graph, bundle, and handoff export/import.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via ExportsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class ExportsMixin:
    @staticmethod
    def _stale_seed_handoff_preflight_arguments() -> dict[str, Any]:
        arguments = DoxaBase._project_brief_default_handoff_preflight_arguments()
        arguments["validation_scope"] = "map"
        return arguments
    def _context_slice_trig(
        self,
        triples: Iterable[ResourceTriple],
        *,
        graph_iri_prefix: str,
    ) -> str:
        dataset = Dataset()
        for prefix, namespace in PREFIXES.items():
            dataset.bind(prefix, namespace)
        dataset.bind("rcg", graph_iri_prefix)
        for triple in triples:
            context = dataset.graph(
                URIRef(self._export_graph_identifier(triple.graph, graph_iri_prefix))
            )
            context.add(
                (
                    self._term_from_row(triple.subject, triple.subject_kind),
                    URIRef(triple.predicate),
                    self._resource_triple_object_term(triple),
                )
            )
        return dataset.serialize(format="trig")
    @staticmethod
    def _draft_query_plan_handoff_kind(
        selected_candidate: QueryTargetCandidate | None,
        *,
        scan: DraftQueryPlanScan,
        binding_requirements: list[DraftQueryPlanBinding],
        storage_environment: DraftQueryPlanStorageEnvironment,
        review_gate: DraftQueryPlanReviewGate,
    ) -> str:
        if selected_candidate is None:
            return "no_query_target"

        blocking_reason_codes = set(review_gate.blocking_reason_codes)
        if "physical_layout_storage_protocol_mismatch" in blocking_reason_codes:
            return "metadata_review_required"
        if scan.relation_identifier is not None:
            return "database_relation_handoff"
        if (
            "query_context_has_other_blockers" in blocking_reason_codes
            and review_gate.direct_review_required is False
        ):
            return "context_review_required"
        if "s3_access_resolution_unrecorded" in blocking_reason_codes:
            return "runtime_resolution_required"
        if not review_gate.executable_without_review:
            return "metadata_review_required"
        if storage_environment.runtime_resolution_required:
            return "runtime_resolution_required"
        if any(binding.required for binding in binding_requirements):
            return "binding_values_required"
        if review_gate.ready_for_execution_attempt:
            return "execution_attempt_ready"
        return "metadata_review_required"
    def _draft_query_plan_handoff_summary(
        self,
        *,
        handoff_kind: str,
        source_context: DraftQueryPlanSourceContext,
        scan: DraftQueryPlanScan,
        review_gate: DraftQueryPlanReviewGate,
        required_bindings: list[str],
        issues: list[QueryPlanningIssue],
        analysis_warnings: list[QueryPlanningIssue],
        caveats: list[CaveatDescription],
    ) -> DraftQueryPlanHandoffSummary:
        primary_repair_cue = self._draft_query_plan_primary_repair_cue(issues)
        return DraftQueryPlanHandoffSummary(
            handoff_kind=handoff_kind,
            selected_candidate_index=source_context.selected_candidate_index,
            selected_candidate_selector=source_context.selected_candidate_selector,
            selected_candidate_note=source_context.selected_candidate_note,
            scan_function=scan.function,
            uri_template=scan.uri_template,
            relation_identifier=scan.relation_identifier,
            connection_reference=scan.connection_reference,
            candidate_path_status=scan.candidate_path_status,
            executable_without_review=review_gate.executable_without_review,
            ready_for_execution_attempt=review_gate.ready_for_execution_attempt,
            primary_execution_attempt_blocking_reason_code=(
                review_gate.primary_execution_attempt_blocking_reason_code
            ),
            execution_attempt_blocking_reason_codes=list(
                review_gate.execution_attempt_blocking_reason_codes
            ),
            runtime_resolution_required=review_gate.runtime_resolution_required,
            binding_values_required=review_gate.binding_values_required,
            required_bindings=list(required_bindings),
            all_issue_codes=list(review_gate.all_issue_codes),
            context_blocked_candidate_allowed=(
                review_gate.context_blocked_candidate_allowed
            ),
            context_blocked_candidate_used=(
                review_gate.context_blocked_candidate_used
            ),
            direct_blocking_reason_codes=list(
                review_gate.direct_blocking_reason_codes
            ),
            context_blocking_reason_codes=list(
                review_gate.context_blocking_reason_codes
            ),
            analysis_warning_count=len(analysis_warnings),
            caveat_count=len(caveats),
            unselected_ready_candidate_indexes=list(
                source_context.unselected_ready_candidate_indexes
            ),
            unselected_direct_clean_candidate_indexes=list(
                source_context.unselected_direct_clean_candidate_indexes
            ),
            selection_reason_codes=list(source_context.selection_reason_codes),
            peer_ready_requires_intent_review=(
                source_context.peer_ready_requires_intent_review
            ),
            selection_caution=source_context.selection_caution,
            route_intent_review_candidate_indexes=list(
                source_context.route_intent_review_candidate_indexes
            ),
            route_intent_caution=source_context.route_intent_caution,
            **primary_repair_cue,
        )
    def _suggested_review_export_path(
        self,
        path_prefix: str,
        revision_iris: Iterable[str],
    ) -> str:
        values = [str(value) for value in revision_iris]
        digest_source = "\n".join(values) if values else path_prefix
        digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:12]
        label_source = self._local_name(values[0]) if values else None
        label = re.sub(r"[^A-Za-z0-9]+", "-", label_source or "revision")
        label = label.strip("-").lower() or "revision"
        return f"/tmp/{path_prefix}-{label[:40]}-{digest}.md"
    def import_turtle(
        self,
        source: str | Path,
        *,
        graph: str = "map",
        format: str = "turtle",
        replace: bool = False,
        allow_immutable: bool = False,
    ) -> int:
        self._ensure_mutable(graph, allow_immutable=allow_immutable)
        rdf_graph = self._parse_rdf_payload(
            source,
            format=format,
            payload_name="source",
            parser_context="import_turtle",
        )
        if replace:
            self.clear_graph(graph, allow_immutable=allow_immutable)
        self._ensure_graph(graph)
        return self._insert_graph(graph, rdf_graph)
    def import_trig(
        self,
        source: str | Path,
        *,
        graph_map: dict[str, str] | None = None,
        replace: bool = False,
        allow_immutable: bool = False,
    ) -> dict[str, int]:
        dataset = self._parse_rdf_dataset(
            source,
            format="trig",
            parser_context="import_trig",
        )

        contexts_by_graph: dict[str, list[Graph]] = {}
        for context in dataset.graphs():
            if len(context) == 0:
                continue
            graph_name = self._local_graph_name(str(context.identifier), graph_map)
            self._ensure_mutable(graph_name, allow_immutable=allow_immutable)
            contexts_by_graph.setdefault(graph_name, []).append(context)

        imported: dict[str, int] = {}
        for graph_name, contexts in contexts_by_graph.items():
            if replace:
                self.clear_graph(graph_name, allow_immutable=allow_immutable)
            self._ensure_graph(graph_name)
            for context in contexts:
                imported[graph_name] = imported.get(
                    graph_name,
                    0,
                ) + self._insert_graph(graph_name, context)
        return imported
    def preflight_context_slice_export(
        self,
        seed_iris: Iterable[str] | str,
        *,
        profile: TypingLiteral[
            "dataset_brief",
            "pattern_brief",
            "deep_lore",
            "resource_brief",
        ] = "dataset_brief",
        max_triples: int = 500,
        include_seed_graphs: bool = False,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
        limit: int = 20,
    ) -> ContextSliceExportRecord:
        return self._context_slice_export_record(
            path=None,
            seed_iris=seed_iris,
            profile=profile,
            max_triples=max_triples,
            include_seed_graphs=include_seed_graphs,
            limit=limit,
            overwrite=False,
            graph_iri_prefix=RCG_PREFIX,
            fail_on_sensitive=False,
            fail_on_invalid=False,
            validation_scope=validation_scope,
            write=False,
        )
    def export_context_slice(
        self,
        path: str | Path,
        seed_iris: Iterable[str] | str,
        *,
        profile: TypingLiteral[
            "dataset_brief",
            "pattern_brief",
            "deep_lore",
            "resource_brief",
        ] = "dataset_brief",
        max_triples: int = 500,
        include_seed_graphs: bool = False,
        overwrite: bool = False,
        graph_iri_prefix: str = RCG_PREFIX,
        fail_on_sensitive: bool = False,
        fail_on_invalid: bool = True,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
        limit: int = 20,
    ) -> ContextSliceExportRecord:
        return self._context_slice_export_record(
            path=path,
            seed_iris=seed_iris,
            profile=profile,
            max_triples=max_triples,
            include_seed_graphs=include_seed_graphs,
            limit=limit,
            overwrite=overwrite,
            graph_iri_prefix=graph_iri_prefix,
            fail_on_sensitive=fail_on_sensitive,
            fail_on_invalid=fail_on_invalid,
            validation_scope=validation_scope,
            write=True,
        )
    def _context_slice_export_record(
        self,
        *,
        path: str | Path | None,
        seed_iris: Iterable[str] | str,
        profile: TypingLiteral[
            "dataset_brief",
            "pattern_brief",
            "deep_lore",
            "resource_brief",
        ],
        max_triples: int,
        include_seed_graphs: bool,
        limit: int,
        overwrite: bool,
        graph_iri_prefix: str,
        fail_on_sensitive: bool,
        fail_on_invalid: bool,
        validation_scope: str | None,
        write: bool,
    ) -> ContextSliceExportRecord:
        if limit < 1:
            raise DoxaBaseError("limit must be at least 1")
        context = self.describe_context_slice(
            seed_iris,
            profile=profile,
            max_triples=max_triples,
            include_trig=False,
            graph_iri_prefix=graph_iri_prefix,
        )
        export_triples = [
            triple
            for triple in context.triples
            if include_seed_graphs or triple.graph not in SEED_GRAPH_NAMES
        ]
        export_triples = self._context_slice_export_history_validation_closure(
            export_triples
        )
        graph_counts: dict[str, int] = {}
        for triple in export_triples:
            graph_counts[triple.graph] = graph_counts.get(triple.graph, 0) + 1
        graph_names = list(graph_counts)
        candidate_triple_count = max(
            context.candidate_triple_count,
            len(export_triples),
        )
        sensitive_literal_count, matches, omitted_match_count = (
            self._context_slice_sensitive_matches(export_triples, limit=limit)
        )
        shareability_hint_count, shareability_hint_matches = (
            self._shareability_hint_matches_for_context_triples(
                export_triples,
                export_part="context_slice_export",
                limit=limit,
            )
        )
        shareability_hints = self._shareability_hints_for_context_triples(
            export_triples
        )
        privacy_warnings = self._sensitive_literal_warnings(
            match_count=sensitive_literal_count,
            omitted_match_count=omitted_match_count,
        )
        scanner_note = (
            "Scanner-clean means no selected context-slice export triples matched "
            "DoxaBase's credential-like graph-term patterns; it is not proof that "
            "the slice is shareable or free of user-specific paths, endpoint "
            "details, or confidential project facts."
        )
        truncation_warnings = self._context_slice_export_truncation_warnings(
            context,
            exported_graphs=graph_names,
            include_seed_graphs=include_seed_graphs,
        )
        warnings = [
            *privacy_warnings,
            *self._shareability_hint_warnings(shareability_hints),
            *context.warnings,
            *truncation_warnings,
            scanner_note,
        ]
        if not include_seed_graphs and any(
            triple.graph in SEED_GRAPH_NAMES for triple in context.triples
        ):
            warnings.insert(
                len(privacy_warnings),
                "Immutable seed graph triples were omitted from this context-slice "
                "export. Fresh DoxaBase capsules already contain the standard seed "
                "ontology and shapes.",
            )
        history_revision_iris = self._context_slice_history_revision_iris(
            export_triples
        )
        if "history" in graph_names:
            warnings.insert(
                len(privacy_warnings),
                (
                    "This context-slice export includes history graph triples, "
                    "but it is not a recovery-complete revision handoff because "
                    "context slices do not include SQLite-side revision snapshot "
                    "rows. Use export_handoff_bundle when a receiving capsule "
                    "needs exact applied diffs, stale-drift checks, or staged "
                    "revision recovery."
                ),
            )
        validation = self._export_validation_result(
            graph_names,
            validation_scope=validation_scope,
            default_scope=None,
        )
        validation_warnings = self._export_validation_warnings(validation)
        validation_blocks_export = validation is not None and not validation.conforms
        warnings.extend(validation_warnings)
        self._raise_if_sensitive_export_blocked(
            fail_on_sensitive=fail_on_sensitive,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
        )
        self._raise_if_invalid_export_blocked(
            fail_on_invalid=fail_on_invalid,
            validation=validation,
        )
        bytes_written = 0
        path_value = str(path) if path is not None else None
        if write:
            if path is None:
                raise DoxaBaseError("path is required when writing context slice export")
            data = self._context_slice_trig(
                export_triples,
                graph_iri_prefix=graph_iri_prefix,
            )
            bytes_written = self._write_export(path, data, overwrite=overwrite)
        suggested_next_actions = self._context_slice_export_suggested_actions(
            seed_iris=seed_iris,
            profile=profile,
            max_triples=max_triples,
            candidate_triple_count=context.candidate_triple_count,
            truncated=context.truncated,
            context_suggested_next_actions=context.suggested_next_actions,
            include_seed_graphs=include_seed_graphs,
            fail_on_sensitive=fail_on_sensitive,
            limit=limit,
            write=write,
            would_block_sensitive_export=sensitive_literal_count > 0,
            would_block_invalid_export=validation_blocks_export,
            validation_scope=validation.scope if validation is not None else None,
            includes_history="history" in graph_names,
            revision_iris=history_revision_iris,
        )
        return ContextSliceExportRecord(
            path=path_value,
            format="trig",
            decision=(
                "block"
                if sensitive_literal_count or validation_blocks_export
                else "clean_by_scanner_only"
            ),
            scanner_clean=sensitive_literal_count == 0,
            shareability_review_required=True,
            shareability_review_status="required_not_completed",
            would_block_sensitive_export=sensitive_literal_count > 0,
            handoff_fit=(
                "resource_scoped_review_context_not_recovery_complete"
                if "history" in graph_names
                else "resource_scoped_review_context"
            ),
            profile=context.profile,
            seeds=[
                self._privacy_redacted_resource_summary(seed)
                for seed in context.seeds
            ],
            graphs=graph_names,
            graph_counts=graph_counts,
            triples=len(export_triples),
            candidate_triple_count=candidate_triple_count,
            omitted_triple_count=max(
                candidate_triple_count - len(export_triples),
                0,
            ),
            max_triples=max_triples,
            truncated=context.truncated,
            include_seed_graphs=include_seed_graphs,
            bytes_written=bytes_written,
            sensitive_literal_count=sensitive_literal_count,
            returned_match_count=len(matches),
            omitted_match_count=omitted_match_count,
            limit=limit,
            matches=matches,
            privacy_warnings=privacy_warnings,
            warnings=warnings,
            scanner_note=scanner_note,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[action.call for action in suggested_next_actions],
            validation_scope=validation.scope if validation is not None else None,
            validation_conforms=(
                validation.conforms if validation is not None else None
            ),
            validation_result_count=(
                validation.result_count if validation is not None else 0
            ),
            validation_results=validation.results if validation is not None else [],
            would_block_invalid_export=validation_blocks_export,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
        )
    def _context_slice_export_history_validation_closure(
        self,
        triples: Iterable[ResourceTriple],
    ) -> list[ResourceTriple]:
        selected = list(triples)
        closure_predicates = {
            self.expand_iri("rc:hasGraphPatch"),
            self.expand_iri("rc:hasGraphSnapshot"),
            self.expand_iri("rc:hasValidationResult"),
        }
        closure_types = {
            self.expand_iri("rc:GraphPatch"),
            self.expand_iri("rc:GraphSnapshot"),
            PREFIXES["sh"] + "ValidationResult",
        }
        seen = {self._resource_triple_key(triple) for triple in selected}
        queue: list[str] = []
        queued: set[str] = set()

        def enqueue(subject: str) -> None:
            if subject not in queued:
                queued.add(subject)
                queue.append(subject)

        for triple in selected:
            if triple.graph != "history":
                continue
            if (
                triple.predicate in closure_predicates
                and triple.object_kind in {"uri", "bnode"}
            ):
                enqueue(triple.object)
            if triple.predicate == str(RDF.type) and triple.object in closure_types:
                enqueue(triple.subject)
            elif set(triple.subject_types) & closure_types:
                enqueue(triple.subject)

        while queue:
            subject = queue.pop(0)
            for triple in self._resource_triples(
                ["history"],
                subject=subject,
                limit=None,
            ):
                triple_key = self._resource_triple_key(triple)
                if triple_key in seen:
                    continue
                seen.add(triple_key)
                selected.append(triple)
                if (
                    triple.predicate in closure_predicates
                    and triple.object_kind in {"uri", "bnode"}
                ):
                    enqueue(triple.object)
        return selected
    def _context_slice_export_truncation_warnings(
        self,
        context: ContextSlice,
        *,
        exported_graphs: Iterable[str],
        include_seed_graphs: bool,
    ) -> list[str]:
        if not context.truncated:
            return []
        exported_graph_set = set(exported_graphs)
        selected_graphs = sorted(
            {
                graph
                for resource in context.resources
                for graph in resource.graphs
                if include_seed_graphs or graph not in SEED_GRAPH_NAMES
            }
        )
        omitted_graphs = [
            graph for graph in selected_graphs if graph not in exported_graph_set
        ]
        selected_surface_roles = self._context_slice_surface_roles_for_graphs(
            selected_graphs
        )
        exported_surface_roles = self._context_slice_surface_roles_for_graphs(
            exported_graph_set
        )
        omitted_surface_roles = [
            role
            for role in selected_surface_roles
            if role not in set(exported_surface_roles)
        ]
        return [
            (
                "Context-slice export is truncated: graphs and graph_counts "
                "describe only capped raw triples, not every structured resource "
                "selected by the slice. "
                f"Selected surface roles: {', '.join(selected_surface_roles) or 'none'}. "
                f"Exported graph roles: {', '.join(sorted(exported_graph_set)) or 'none'}. "
                f"Omitted graph roles: {', '.join(omitted_graphs) or 'none'}. "
                f"Omitted surface roles: {', '.join(omitted_surface_roles) or 'none'}. "
                "Rerun this preflight with max_triples="
                f"{context.candidate_triple_count} or narrow the seed/profile "
                "before writing a handoff artifact."
            )
        ]
    def _context_slice_export_suggested_actions(
        self,
        *,
        seed_iris: Iterable[str] | str,
        profile: str,
        max_triples: int,
        candidate_triple_count: int,
        truncated: bool,
        context_suggested_next_actions: Iterable[SuggestedNextAction],
        include_seed_graphs: bool,
        fail_on_sensitive: bool,
        limit: int,
        write: bool,
        would_block_sensitive_export: bool,
        would_block_invalid_export: bool,
        validation_scope: str | None,
        includes_history: bool,
        revision_iris: list[str],
    ) -> list[SuggestedNextAction]:
        actions: list[SuggestedNextAction] = []
        seed_values = self._string_values("seed_iris", seed_iris, required=True)
        resource_brief_retry_keys: set[tuple[tuple[str, ...], int]] = set()
        if not write:
            for context_action in context_suggested_next_actions:
                if context_action.tool_name != "describe_context_slice":
                    continue
                retry_profile = context_action.arguments.get("profile")
                if retry_profile != "resource_brief":
                    continue
                retry_seed_values = self._string_values(
                    "seed_iris",
                    context_action.arguments.get("seed_iris", seed_values),
                    required=True,
                )
                retry_max_triples = int(
                    context_action.arguments.get("max_triples", max_triples)
                )
                retry_key = (tuple(retry_seed_values), retry_max_triples)
                if retry_key in resource_brief_retry_keys:
                    continue
                resource_brief_retry_keys.add(retry_key)
                arguments = {
                    "seed_iris": retry_seed_values,
                    "profile": "resource_brief",
                    "max_triples": retry_max_triples,
                    "include_seed_graphs": include_seed_graphs,
                    "limit": limit,
                }
                actions.append(
                    SuggestedNextAction(
                        action_label="Preflight resource brief retry",
                        tool_name="preflight_context_slice_export",
                        mcp_tool_name="doxabase.preflight_context_slice_export",
                        arguments=arguments,
                        reason=(
                            "The described slice reported that profile-specific "
                            "expansion did not apply. Rerun export preflight "
                            "with resource_brief before writing an under-broad "
                            "context-slice artifact."
                        ),
                        call=self._suggested_call_string(
                            "preflight_context_slice_export",
                            arguments,
                        ),
                    )
                )
        if truncated:
            full_triple_cap = max(candidate_triple_count, max_triples)
            arguments = {
                "seed_iris": seed_values,
                "profile": profile,
                "max_triples": full_triple_cap,
                "include_seed_graphs": include_seed_graphs,
                "limit": limit,
            }
            actions.append(
                SuggestedNextAction(
                    action_label="Preflight full context slice",
                    tool_name="preflight_context_slice_export",
                    mcp_tool_name="doxabase.preflight_context_slice_export",
                    arguments=arguments,
                    reason=(
                        "The current context-slice export is truncated, so "
                        "graphs and graph_counts may omit structured lore "
                        "roles selected by the slice. Rerun the preflight with "
                        "the full candidate triple cap before writing a handoff "
                        "artifact, or narrow the seed/profile first."
                    ),
                    call=self._suggested_call_string(
                        "preflight_context_slice_export",
                        arguments,
                    ),
                )
            )
        if would_block_invalid_export and validation_scope is not None:
            arguments = {
                "scope": validation_scope,
                "limit_results": max(limit, 20),
            }
            actions.append(
                SuggestedNextAction(
                    action_label="Inspect context-slice validation failures",
                    tool_name="validate_graph",
                    mcp_tool_name="doxabase.validate_graph",
                    arguments=arguments,
                    reason=(
                        "The live graph validation gate failed for the graph "
                        "roles selected by this context slice. Inspect SHACL "
                        "diagnostics and repair the graph before writing an "
                        "importable slice."
                    ),
                    call=self._suggested_call_string(
                        "validate_graph",
                        arguments,
                    ),
                )
            )
        if would_block_sensitive_export:
            inspect_arguments = {
                "seed_iris": seed_values,
                "profile": profile,
                "max_triples": max_triples,
                "privacy_scan_limit": limit,
            }
            actions.append(
                SuggestedNextAction(
                    action_label="Inspect blocked context slice",
                    tool_name="describe_context_slice",
                    mcp_tool_name="doxabase.describe_context_slice",
                    arguments=inspect_arguments,
                    reason=(
                        "The context-slice export preflight found redacted "
                        "sensitive-looking terms. Inspect the selected slice "
                        "locally, then narrow to clean seed resources or scrub "
                        "project content before writing an artifact."
                    ),
                    call=self._suggested_call_string(
                        "describe_context_slice",
                        inspect_arguments,
                    ),
                )
            )
            if not includes_history:
                preflight_arguments = {
                    "export_kind": "handoff_bundle",
                    "graphs": ["project"],
                    "limit": limit,
                }
                actions.append(
                    SuggestedNextAction(
                        action_label="Preflight project export privacy",
                        tool_name="export_preflight",
                        mcp_tool_name="doxabase.export_preflight",
                        arguments=preflight_arguments,
                        reason=(
                            "The resource-scoped slice is blocked by privacy "
                            "matches. Run the broader redacted export preflight "
                            "before choosing whether to narrow scope, scrub "
                            "content, or defer sharing."
                        ),
                        call=self._suggested_call_string(
                            "export_preflight",
                            preflight_arguments,
                        ),
                    )
                )
        if (
            not write
            and not would_block_sensitive_export
            and not would_block_invalid_export
        ):
            digest_source = "\n".join(seed_values)
            digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:12]
            label_source = self._local_name(seed_values[0]) if seed_values else None
            label = re.sub(r"[^A-Za-z0-9]+", "-", label_source or "context-slice")
            label = label.strip("-").lower() or "context-slice"
            arguments = {
                "path": f"/tmp/context-slice-{label[:40]}-{digest}.trig",
                "seed_iris": seed_values,
                "profile": profile,
                "max_triples": max_triples,
                "include_seed_graphs": include_seed_graphs,
                "fail_on_sensitive": True,
                "fail_on_invalid": True,
            }
            if fail_on_sensitive:
                arguments["fail_on_sensitive"] = fail_on_sensitive
            if validation_scope is not None:
                arguments["validation_scope"] = validation_scope
            actions.append(
                SuggestedNextAction(
                    action_label="Export context slice",
                    tool_name="export_context_slice",
                    mcp_tool_name="doxabase.export_context_slice",
                    arguments=arguments,
                    reason=(
                        "Write an importable TriG bundle for only the selected "
                        "context-slice triples after reviewing the preflight scan."
                    ),
                    call=self._suggested_call_string(
                        "export_context_slice",
                        arguments,
                    ),
                )
            )
        if includes_history:
            handoff_arguments: dict[str, Any]
            if would_block_sensitive_export or would_block_invalid_export:
                handoff_arguments = {
                    "export_kind": "handoff_bundle",
                    "graphs": ["project"],
                    "limit": limit,
                }
                if validation_scope is not None:
                    handoff_arguments["validation_scope"] = validation_scope
            else:
                handoff_arguments = {
                    "trig_path": "<project-handoff.trig>",
                    "revision_snapshot_path": "<revision-snapshots.json>",
                    "manifest_path": "<handoff-manifest.json>",
                    "graphs": ["project"],
                    "fail_on_sensitive": True,
                    "fail_on_invalid": True,
                }
                if validation_scope is not None:
                    handoff_arguments["validation_scope"] = validation_scope
            if revision_iris:
                handoff_arguments["revision_iris"] = revision_iris
            if would_block_sensitive_export or would_block_invalid_export:
                tool_name = "export_preflight"
                action_label = "Preflight recovery handoff bundle"
                reason = (
                    "The selected history-bearing context slice is blocked by "
                    "privacy or validation review, so resolve the preflight "
                    "before writing recovery-complete handoff artifacts."
                )
            else:
                tool_name = "export_handoff_bundle"
                action_label = "Export recovery handoff bundle"
                reason = (
                    "History-bearing context slices are importable review "
                    "context but do not carry revision snapshot rows; use a "
                    "handoff bundle for exact revision recovery in another "
                    "capsule."
                )
            placeholder_fields = [
                field
                for field in (
                    "trig_path",
                    "revision_snapshot_path",
                    "manifest_path",
                )
                if field in handoff_arguments
            ]
            action_class = (
                SuggestedNextAction
                if would_block_sensitive_export or would_block_invalid_export
                else TemplatedSuggestedNextAction
            )
            action_kwargs: dict[str, Any] = {}
            if not would_block_sensitive_export and not would_block_invalid_export:
                action_kwargs = {
                    "required_extra_arguments": placeholder_fields,
                    "placeholder_fields": placeholder_fields,
                    "reviewed_value_fields": placeholder_fields,
                }
            actions.append(
                action_class(
                    action_label=action_label,
                    tool_name=tool_name,
                    mcp_tool_name=f"doxabase.{tool_name}",
                    arguments=handoff_arguments,
                    reason=reason,
                    call=self._suggested_call_string(
                        tool_name,
                        handoff_arguments,
                    ),
                    **action_kwargs,
                )
            )
        return actions
    @staticmethod
    def _default_graph_export_validation_scope(graph_names: list[str]) -> str:
        graph_set = set(graph_names)
        if graph_set <= {"map"}:
            return "map"
        if graph_set <= {"base_ontology", "ontology"}:
            return "ontology"
        if graph_set <= {"base_shapes", "shapes"}:
            return "shapes"
        if graph_set <= {
            "base_ontology",
            "ontology",
            "observations",
            "patterns",
            "evidence",
        }:
            return "patterns"
        return "all"
    def _export_validation_result(
        self,
        graph_names: list[str],
        *,
        validation_scope: str | None,
        default_scope: str | None,
        limit_results: int = 20,
    ) -> ValidationResult | None:
        if not graph_names:
            return None
        scope = (
            validation_scope
            or default_scope
            or self._default_graph_export_validation_scope(graph_names)
        )
        return self.validate_graph(scope=scope, limit_results=limit_results)  # type: ignore[arg-type]
    @staticmethod
    def _export_validation_warnings(
        validation: ValidationResult | None,
    ) -> list[str]:
        if validation is None or validation.conforms:
            return []
        return [
            "Export validation failed for scope "
            f"{validation.scope!r} with {validation.result_count} SHACL "
            "result(s). Run validate_graph for that scope before exporting, "
            "or pass fail_on_invalid=False only for a deliberately reviewed "
            "invalid artifact."
        ]
    @staticmethod
    def _raise_if_invalid_export_blocked(
        *,
        fail_on_invalid: bool,
        validation: ValidationResult | None,
    ) -> None:
        if not fail_on_invalid or validation is None or validation.conforms:
            return
        raise DoxaBaseError(
            "Export blocked because fail_on_invalid=True and validation "
            f"scope {validation.scope!r} produced {validation.result_count} "
            "SHACL result(s). Run validate_graph before exporting, or pass "
            "fail_on_invalid=False only for a deliberately reviewed invalid "
            "artifact."
        )
    def export_preflight(
        self,
        *,
        export_kind: TypingLiteral[
            "graph",
            "trig",
            "revision_snapshots",
            "handoff_bundle",
        ] = "handoff_bundle",
        graphs: Iterable[str] | str | None = None,
        revision_iris: Iterable[str] | str | None = None,
        snapshot_graph_roles: Iterable[str] | str | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
        limit: int = 20,
    ) -> ExportPreflightRecord:
        if limit < 1:
            raise DoxaBaseError("limit must be at least 1")
        if export_kind not in {
            "graph",
            "trig",
            "revision_snapshots",
            "handoff_bundle",
        }:
            raise DoxaBaseError(
                "export_kind must be one of: graph, trig, "
                "revision_snapshots, handoff_bundle"
            )
        if export_kind == "revision_snapshots" and graphs is not None:
            raise DoxaBaseError(
                "graphs applies to graph, trig, and handoff_bundle preflights; "
                "use snapshot_graph_roles for revision_snapshots."
            )

        graph_names: list[str] = []
        if export_kind == "graph":
            graph_names = self._graph_names_for_export(
                graphs if graphs is not None else "map",
            )
        elif export_kind in {"trig", "handoff_bundle"}:
            graph_names = self._graph_names_for_export(
                graphs,
                default_preset="project",
            )

        expanded_revisions: list[str] = []
        snapshot_entries: list[dict[str, Any]] = []
        if export_kind in {"revision_snapshots", "handoff_bundle"}:
            revisions = [
                self._required_iri("revision_iris", value)
                for value in self._string_values("revision_iris", revision_iris)
            ]
            expanded_revisions = self._snapshot_export_revision_iris(revisions)
            snapshot_roles = self._snapshot_bundle_graph_roles(snapshot_graph_roles)
            snapshot_entries = self._graph_snapshot_bundle_entries(
                revision_iris=expanded_revisions or None,
                graph_roles=snapshot_roles or None,
            )

        graph_scan: SensitiveLiteralScan | None = None
        graph_matches: list[ExportPreflightMatch] = []
        graph_sensitive_count = 0
        graph_privacy_warnings: list[str] = []
        graph_shareability_hints: list[str] = []
        graph_shareability_hint_count = 0
        graph_shareability_hint_matches: list[ShareabilityHintMatch] = []
        if graph_names:
            graph_scan = self.scan_sensitive_literals(graph_names, limit=limit)
            graph_matches = self._export_preflight_graph_matches(graph_scan.matches)
            graph_sensitive_count, graph_privacy_warnings = (
                self._export_privacy_warnings(graph_names)
            )
            graph_shareability_hints = self._shareability_hints_for_graphs(
                graph_names
            )
            graph_shareability_hint_count, graph_shareability_hint_matches = (
                self._shareability_hint_matches_for_graphs(
                    graph_names,
                    export_part="graphs",
                    limit=limit,
                )
            )
        validation = self._export_validation_result(
            graph_names,
            validation_scope=validation_scope,
            default_scope=(
                "all" if export_kind in {"trig", "handoff_bundle"} else None
            ),
        )
        validation_warnings = self._export_validation_warnings(validation)

        snapshot_match_limit = max(0, limit - len(graph_matches))
        snapshot_sensitive_count, snapshot_matches = (
            self._revision_snapshot_sensitive_matches(
                snapshot_entries,
                limit=snapshot_match_limit,
            )
        )
        _snapshot_warning_count, snapshot_privacy_warnings = (
            self._revision_snapshot_export_privacy_warnings(snapshot_entries)
        )
        snapshot_shareability_hints = self._shareability_hints_for_snapshot_entries(
            snapshot_entries
        )
        snapshot_shareability_match_limit = max(
            0,
            limit - len(graph_shareability_hint_matches),
        )
        snapshot_shareability_hint_count, snapshot_shareability_hint_matches = (
            self._shareability_hint_matches_for_snapshot_entries(
                snapshot_entries,
                limit=snapshot_shareability_match_limit,
            )
        )

        matches = [*graph_matches, *snapshot_matches]
        shareability_hint_matches = [
            *graph_shareability_hint_matches,
            *snapshot_shareability_hint_matches,
        ]
        shareability_hint_count = (
            graph_shareability_hint_count + snapshot_shareability_hint_count
        )
        sensitive_literal_count = graph_sensitive_count + snapshot_sensitive_count
        privacy_warnings = [
            *graph_privacy_warnings,
            *snapshot_privacy_warnings,
        ]
        shareability_hints = list(
            dict.fromkeys([*graph_shareability_hints, *snapshot_shareability_hints])
        )
        scanner_note = (
            "Scanner-clean means no selected export content matched DoxaBase's "
            "credential-like graph-term patterns; it is not proof that an artifact "
            "is shareable or free of user-specific paths, endpoint details, or "
            "confidential project facts."
        )
        scanner_clean = sensitive_literal_count == 0
        export_scope_warnings = self._export_scope_warnings(
            export_kind=export_kind,
            graph_names=graph_names,
        )
        warnings = [*privacy_warnings, *validation_warnings, *export_scope_warnings]
        if scanner_clean:
            warnings.append(scanner_note)
        warnings[0:0] = self._shareability_hint_warnings(shareability_hints)
        validation_blocks_export = validation is not None and not validation.conforms
        snapshot_revision_iris = list(
            dict.fromkeys(entry["revision_iri"] for entry in snapshot_entries)
        )
        snapshot_graph_role_values = list(
            dict.fromkeys(entry["graph_role"] for entry in snapshot_entries)
        )
        record = ExportPreflightRecord(
            export_kind=export_kind,
            decision=(
                "block"
                if sensitive_literal_count or validation_blocks_export
                else "clean_by_scanner_only"
            ),
            scanner_clean=scanner_clean,
            shareability_review_required=True,
            shareability_review_status="required_not_completed",
            would_block_sensitive_export=sensitive_literal_count > 0,
            graphs=graph_names,
            graph_counts=self._graph_counts(graph_names),
            revision_iris=snapshot_revision_iris,
            snapshot_graph_roles=snapshot_graph_role_values,
            snapshot_count=len(snapshot_entries),
            snapshot_quad_count=sum(len(entry["quads"]) for entry in snapshot_entries),
            sensitive_literal_count=sensitive_literal_count,
            graph_sensitive_literal_count=graph_sensitive_count,
            snapshot_sensitive_literal_count=snapshot_sensitive_count,
            returned_match_count=len(matches),
            omitted_match_count=max(0, sensitive_literal_count - len(matches)),
            limit=limit,
            matches=matches,
            privacy_warnings=privacy_warnings,
            warnings=warnings,
            scanner_note=scanner_note,
            suggested_next_actions=[],
            suggested_next_calls=[],
            validation_scope=validation.scope if validation is not None else None,
            validation_conforms=(
                validation.conforms if validation is not None else None
            ),
            validation_result_count=(
                validation.result_count if validation is not None else 0
            ),
            validation_results=validation.results if validation is not None else [],
            would_block_invalid_export=validation_blocks_export,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
        )
        actions = self._export_preflight_suggested_actions(record)
        return replace(
            record,
            suggested_next_actions=actions,
            suggested_next_calls=[action.call for action in actions],
        )
    def export_revision_snapshots(
        self,
        path: str | Path,
        *,
        revision_iris: Iterable[str] | str | None = None,
        graph_roles: Iterable[str] | str | None = None,
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
    ) -> RevisionSnapshotBundleExportRecord:
        revisions = [
            self._required_iri("revision_iris", value)
            for value in self._string_values("revision_iris", revision_iris)
        ]
        expanded_revisions = self._snapshot_export_revision_iris(revisions)
        roles = self._snapshot_bundle_graph_roles(graph_roles)
        entries = self._graph_snapshot_bundle_entries(
            revision_iris=expanded_revisions or None,
            graph_roles=roles or None,
        )
        revision_values = list(dict.fromkeys(entry["revision_iri"] for entry in entries))
        graph_role_values = list(dict.fromkeys(entry["graph_role"] for entry in entries))
        quad_count = sum(len(entry["quads"]) for entry in entries)
        sensitive_literal_count, privacy_warnings = (
            self._revision_snapshot_export_privacy_warnings(entries)
        )
        shareability_hints = self._shareability_hints_for_snapshot_entries(entries)
        shareability_hint_count, shareability_hint_matches = (
            self._shareability_hint_matches_for_snapshot_entries(entries)
        )
        self._raise_if_sensitive_export_blocked(
            fail_on_sensitive=fail_on_sensitive,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
        )
        payload = {
            "format": "doxabase.revision_snapshot_bundle.v1",
            "created_at": _now(),
            "snapshots": entries,
        }
        data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        bytes_written = self._write_export(path, data, overwrite=overwrite)
        return RevisionSnapshotBundleExportRecord(
            path=str(path),
            format=payload["format"],
            revision_iris=revision_values,
            graph_roles=graph_role_values,
            snapshot_count=len(entries),
            quad_count=quad_count,
            bytes_written=bytes_written,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
        )
    @staticmethod
    def _export_scope_warnings(
        *,
        export_kind: str,
        graph_names: list[str],
    ) -> list[str]:
        if export_kind != "trig":
            return []
        if graph_names != list(EXPORT_PRESETS["workflow"]):
            return []
        return [
            "This is review context only: it omits history and revision snapshot "
            "rows. Use export_handoff_bundle or project TriG plus "
            "export_revision_snapshots for recovery."
        ]
    @staticmethod
    def _trig_export_artifact_kind(graph_names: list[str]) -> str:
        if graph_names == list(EXPORT_PRESETS["workflow"]):
            return "workflow_review_trig"
        if graph_names == list(EXPORT_PRESETS["project"]):
            return "project_trig"
        if any(graph in SEED_GRAPH_NAMES for graph in graph_names):
            return "trig_with_seed_graphs"
        return "custom_trig"
    def export_handoff_bundle(
        self,
        trig_path: str | Path,
        revision_snapshot_path: str | Path,
        *,
        manifest_path: str | Path | None = None,
        graphs: Iterable[str] | str | None = None,
        revision_iris: Iterable[str] | str | None = None,
        snapshot_graph_roles: Iterable[str] | str | None = None,
        overwrite: bool = False,
        graph_iri_prefix: str = RCG_PREFIX,
        fail_on_sensitive: bool = False,
        fail_on_invalid: bool = True,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> HandoffBundleExportRecord:
        self._preflight_handoff_bundle_export_paths(
            trig_path,
            revision_snapshot_path,
            manifest_path,
            overwrite=overwrite,
        )
        graph_names = self._graph_names_for_export(
            graphs,
            default_preset="project",
        )
        revisions = [
            self._required_iri("revision_iris", value)
            for value in self._string_values("revision_iris", revision_iris)
        ]
        expanded_revisions = self._snapshot_export_revision_iris(revisions)
        snapshot_roles = self._snapshot_bundle_graph_roles(snapshot_graph_roles)
        snapshot_entries = self._graph_snapshot_bundle_entries(
            revision_iris=expanded_revisions or None,
            graph_roles=snapshot_roles or None,
        )
        snapshot_revision_iris = list(
            dict.fromkeys(entry["revision_iri"] for entry in snapshot_entries)
        )
        snapshot_graph_role_values = list(
            dict.fromkeys(entry["graph_role"] for entry in snapshot_entries)
        )
        snapshot_quad_count = sum(len(entry["quads"]) for entry in snapshot_entries)
        recovery_sessions = self._handoff_bundle_recovery_session_manifest_entries(
            snapshot_revision_iris
        )
        trig_sensitive_count, trig_privacy_warnings = self._export_privacy_warnings(
            graph_names
        )
        trig_shareability_hints = self._shareability_hints_for_graphs(graph_names)
        trig_shareability_hint_count, trig_shareability_hint_matches = (
            self._shareability_hint_matches_for_graphs(graph_names)
        )
        snapshot_sensitive_count, snapshot_privacy_warnings = (
            self._revision_snapshot_export_privacy_warnings(snapshot_entries)
        )
        snapshot_shareability_hints = self._shareability_hints_for_snapshot_entries(
            snapshot_entries
        )
        snapshot_shareability_match_limit = max(
            0,
            DEFAULT_SHAREABILITY_HINT_MATCH_LIMIT
            - len(trig_shareability_hint_matches),
        )
        snapshot_shareability_hint_count, snapshot_shareability_hint_matches = (
            self._shareability_hint_matches_for_snapshot_entries(
                snapshot_entries,
                limit=snapshot_shareability_match_limit,
            )
        )
        shareability_hint_count = (
            trig_shareability_hint_count + snapshot_shareability_hint_count
        )
        shareability_hint_matches = [
            *trig_shareability_hint_matches,
            *snapshot_shareability_hint_matches,
        ]
        sensitive_literal_count = trig_sensitive_count + snapshot_sensitive_count
        privacy_warnings = [
            *trig_privacy_warnings,
            *snapshot_privacy_warnings,
        ]
        shareability_hints = list(
            dict.fromkeys([*trig_shareability_hints, *snapshot_shareability_hints])
        )
        validation = self._export_validation_result(
            graph_names,
            validation_scope=validation_scope,
            default_scope="all",
        )
        validation_warnings = self._export_validation_warnings(validation)
        validation_blocks_export = validation is not None and not validation.conforms
        decision = (
            "block"
            if sensitive_literal_count or validation_blocks_export
            else "clean_by_scanner_only"
        )
        scanner_clean = sensitive_literal_count == 0
        shareability_review_required = True
        shareability_review_status = "required_not_completed"
        would_block_sensitive_export = sensitive_literal_count > 0
        scanner_note = (
            "Scanner-clean means no selected export content matched DoxaBase's "
            "credential-like graph-term patterns; it is not proof that an artifact "
            "is shareable or free of user-specific paths, endpoint details, or "
            "confidential project facts."
        )
        warnings = [
            *privacy_warnings,
            *validation_warnings,
            *self._shareability_hint_warnings(shareability_hints),
            scanner_note,
        ]
        self._raise_if_sensitive_export_blocked(
            fail_on_sensitive=fail_on_sensitive,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
        )
        self._raise_if_invalid_export_blocked(
            fail_on_invalid=fail_on_invalid,
            validation=validation,
        )

        dataset = self.to_dataset(graph_names, graph_iri_prefix=graph_iri_prefix)
        trig_data = dataset.serialize(format="trig")
        snapshot_payload = {
            "format": "doxabase.revision_snapshot_bundle.v1",
            "created_at": _now(),
            "snapshots": snapshot_entries,
        }
        snapshot_data = json.dumps(snapshot_payload, indent=2, sort_keys=True) + "\n"
        trig_bytes_written = self._write_export(
            trig_path,
            trig_data,
            overwrite=overwrite,
        )
        snapshot_bytes_written = self._write_export(
            revision_snapshot_path,
            snapshot_data,
            overwrite=overwrite,
        )
        trig_record = GraphExportRecord(
            path=str(trig_path),
            format="trig",
            graphs=graph_names,
            graph_counts=self._graph_counts(graph_names),
            triples=len(dataset),
            bytes_written=trig_bytes_written,
            sensitive_literal_count=trig_sensitive_count,
            privacy_warnings=trig_privacy_warnings,
            warnings=[
                *trig_privacy_warnings,
                *validation_warnings,
                *self._shareability_hint_warnings(trig_shareability_hints),
            ],
            validation_scope=validation.scope if validation is not None else None,
            validation_conforms=(
                validation.conforms if validation is not None else None
            ),
            validation_result_count=(
                validation.result_count if validation is not None else 0
            ),
            validation_results=validation.results if validation is not None else [],
            would_block_invalid_export=validation_blocks_export,
            artifact_kind="handoff_trig",
            recommended_import_tool="doxabase.import_trig",
            recovery_complete=False,
            shareability_hints=trig_shareability_hints,
            shareability_hint_count=trig_shareability_hint_count,
            returned_shareability_hint_count=len(trig_shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                trig_shareability_hint_count - len(trig_shareability_hint_matches),
            ),
            shareability_hint_matches=trig_shareability_hint_matches,
        )
        snapshot_record = RevisionSnapshotBundleExportRecord(
            path=str(revision_snapshot_path),
            format=snapshot_payload["format"],
            revision_iris=snapshot_revision_iris,
            graph_roles=snapshot_graph_role_values,
            snapshot_count=len(snapshot_entries),
            quad_count=snapshot_quad_count,
            bytes_written=snapshot_bytes_written,
            sensitive_literal_count=snapshot_sensitive_count,
            privacy_warnings=snapshot_privacy_warnings,
            shareability_hints=snapshot_shareability_hints,
            shareability_hint_count=snapshot_shareability_hint_count,
            returned_shareability_hint_count=len(snapshot_shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                snapshot_shareability_hint_count
                - len(snapshot_shareability_hint_matches),
            ),
            shareability_hint_matches=snapshot_shareability_hint_matches,
        )
        recommended_import_tool = (
            "doxabase.import_handoff_bundle"
            if manifest_path is not None
            else "doxabase.import_trig then doxabase.import_revision_snapshots"
        )
        manifest = self._handoff_bundle_manifest(
            trig=trig_record,
            revision_snapshots=snapshot_record,
            decision=decision,
            scanner_clean=scanner_clean,
            shareability_review_required=shareability_review_required,
            shareability_review_status=shareability_review_status,
            would_block_sensitive_export=would_block_sensitive_export,
            sensitive_literal_count=sensitive_literal_count,
            graph_sensitive_literal_count=trig_sensitive_count,
            snapshot_sensitive_literal_count=snapshot_sensitive_count,
            privacy_warnings=privacy_warnings,
            warnings=warnings,
            scanner_note=scanner_note,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
            recommended_import_tool=recommended_import_tool,
            validation_scope=validation.scope if validation is not None else None,
            validation_conforms=(
                validation.conforms if validation is not None else None
            ),
            validation_result_count=(
                validation.result_count if validation is not None else 0
            ),
            validation_results=validation.results if validation is not None else [],
            would_block_invalid_export=validation_blocks_export,
            recovery_sessions=recovery_sessions,
        )
        manifest_bytes_written = None
        if manifest_path is not None:
            manifest_data = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
            manifest_bytes_written = self._write_export(
                manifest_path,
                manifest_data,
                overwrite=overwrite,
            )
        return HandoffBundleExportRecord(
            trig=trig_record,
            revision_snapshots=snapshot_record,
            paths={
                "trig": str(trig_path),
                "revision_snapshots": str(revision_snapshot_path),
                **(
                    {"manifest": str(manifest_path)}
                    if manifest_path is not None
                    else {}
                ),
            },
            manifest=manifest,
            graph_roles=graph_names,
            snapshot_graph_roles=snapshot_graph_role_values,
            revision_iris=snapshot_revision_iris,
            manifest_path=str(manifest_path) if manifest_path is not None else None,
            manifest_bytes_written=manifest_bytes_written,
            decision=decision,
            scanner_clean=scanner_clean,
            shareability_review_required=shareability_review_required,
            shareability_review_status=shareability_review_status,
            would_block_sensitive_export=would_block_sensitive_export,
            sensitive_literal_count=sensitive_literal_count,
            graph_sensitive_literal_count=trig_sensitive_count,
            snapshot_sensitive_literal_count=snapshot_sensitive_count,
            privacy_warnings=privacy_warnings,
            warnings=warnings,
            scanner_note=scanner_note,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
            recommended_import_tool=recommended_import_tool,
            validation_scope=validation.scope if validation is not None else None,
            validation_conforms=(
                validation.conforms if validation is not None else None
            ),
            validation_result_count=(
                validation.result_count if validation is not None else 0
            ),
            validation_results=validation.results if validation is not None else [],
            would_block_invalid_export=validation_blocks_export,
        )
    @staticmethod
    def _handoff_bundle_manifest(
        *,
        trig: GraphExportRecord,
        revision_snapshots: RevisionSnapshotBundleExportRecord,
        decision: str,
        scanner_clean: bool,
        shareability_review_required: bool,
        shareability_review_status: str,
        would_block_sensitive_export: bool,
        sensitive_literal_count: int,
        graph_sensitive_literal_count: int,
        snapshot_sensitive_literal_count: int,
        privacy_warnings: list[str],
        warnings: list[str],
        scanner_note: str,
        shareability_hints: list[str],
        shareability_hint_count: int,
        returned_shareability_hint_count: int,
        omitted_shareability_hint_count: int,
        shareability_hint_matches: list[ShareabilityHintMatch],
        recommended_import_tool: str,
        validation_scope: str | None,
        validation_conforms: bool | None,
        validation_result_count: int,
        validation_results: list[ValidationDiagnostic],
        would_block_invalid_export: bool,
        recovery_sessions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        recovery_session_iris = [
            str(session["session_iri"])
            for session in recovery_sessions
            if isinstance(session.get("session_iri"), str)
        ]
        return {
            "format": "doxabase.handoff_bundle.v1",
            "created_at": _now(),
            "artifacts": {
                "trig": {
                    "path": trig.path,
                    "format": trig.format,
                    "artifact_kind": trig.artifact_kind,
                    "importable": trig.importable,
                    "recommended_import_tool": trig.recommended_import_tool,
                    "recovery_complete": trig.recovery_complete,
                    "graph_roles": trig.graphs,
                    "graph_counts": trig.graph_counts,
                    "triples": trig.triples,
                    "bytes_written": trig.bytes_written,
                    "sensitive_literal_count": trig.sensitive_literal_count,
                    "privacy_warnings": trig.privacy_warnings,
                    "validation_scope": trig.validation_scope,
                    "validation_conforms": trig.validation_conforms,
                    "validation_result_count": trig.validation_result_count,
                    "validation_results": to_jsonable(trig.validation_results),
                    "would_block_invalid_export": trig.would_block_invalid_export,
                    "shareability_hints": trig.shareability_hints,
                    "shareability_hint_count": trig.shareability_hint_count,
                    "returned_shareability_hint_count": (
                        trig.returned_shareability_hint_count
                    ),
                    "omitted_shareability_hint_count": (
                        trig.omitted_shareability_hint_count
                    ),
                    "shareability_hint_matches": to_jsonable(
                        trig.shareability_hint_matches
                    ),
                    "artifact_disposition": trig.artifact_disposition,
                    "git_safe": trig.git_safe,
                },
                "revision_snapshots": {
                    "path": revision_snapshots.path,
                    "format": revision_snapshots.format,
                    "artifact_kind": revision_snapshots.artifact_kind,
                    "importable": revision_snapshots.importable,
                    "recommended_import_tool": (
                        revision_snapshots.recommended_import_tool
                    ),
                    "recovery_complete": revision_snapshots.recovery_complete,
                    "revision_iris": revision_snapshots.revision_iris,
                    "graph_roles": revision_snapshots.graph_roles,
                    "snapshot_count": revision_snapshots.snapshot_count,
                    "quad_count": revision_snapshots.quad_count,
                    "bytes_written": revision_snapshots.bytes_written,
                    "sensitive_literal_count": (
                        revision_snapshots.sensitive_literal_count
                    ),
                    "privacy_warnings": revision_snapshots.privacy_warnings,
                    "shareability_hints": revision_snapshots.shareability_hints,
                    "shareability_hint_count": (
                        revision_snapshots.shareability_hint_count
                    ),
                    "returned_shareability_hint_count": (
                        revision_snapshots.returned_shareability_hint_count
                    ),
                    "omitted_shareability_hint_count": (
                        revision_snapshots.omitted_shareability_hint_count
                    ),
                    "shareability_hint_matches": to_jsonable(
                        revision_snapshots.shareability_hint_matches
                    ),
                    "artifact_disposition": (
                        revision_snapshots.artifact_disposition
                    ),
                    "git_safe": revision_snapshots.git_safe,
                },
            },
            "recommended_import_sequence": [
                {
                    "step": 1,
                    "tool_name": "import_trig",
                    "mcp_tool_name": "doxabase.import_trig",
                    "path": trig.path,
                    "expected_snapshot_evidence_status": (
                        "history_only_count_digest"
                    ),
                },
                {
                    "step": 2,
                    "tool_name": "import_revision_snapshots",
                    "mcp_tool_name": "doxabase.import_revision_snapshots",
                    "path": revision_snapshots.path,
                    "expected_snapshot_evidence_status": (
                        "history_plus_snapshot_rows"
                    ),
                },
            ],
            "artifact_kind": "handoff_bundle",
            "importable": True,
            "recommended_import_tool": recommended_import_tool,
            "recovery_complete": True,
            "json_first_status": "snapshot_rows_without_history",
            "final_snapshot_evidence_status": "history_plus_snapshot_rows",
            "revision_iris": revision_snapshots.revision_iris,
            "snapshot_graph_roles": revision_snapshots.graph_roles,
            "recovery_session_count": len(recovery_sessions),
            "recovery_session_iris": recovery_session_iris,
            "recovery_sessions": recovery_sessions,
            "decision": decision,
            "scanner_clean": scanner_clean,
            "shareability_review_required": shareability_review_required,
            "shareability_review_status": shareability_review_status,
            "would_block_sensitive_export": would_block_sensitive_export,
            "would_block_invalid_export": would_block_invalid_export,
            "sensitive_literal_count": sensitive_literal_count,
            "graph_sensitive_literal_count": graph_sensitive_literal_count,
            "snapshot_sensitive_literal_count": snapshot_sensitive_literal_count,
            "privacy_warnings": privacy_warnings,
            "validation_scope": validation_scope,
            "validation_conforms": validation_conforms,
            "validation_result_count": validation_result_count,
            "validation_results": to_jsonable(validation_results),
            "warnings": warnings,
            "scanner_note": scanner_note,
            "shareability_hints": shareability_hints,
            "shareability_hint_count": shareability_hint_count,
            "returned_shareability_hint_count": returned_shareability_hint_count,
            "omitted_shareability_hint_count": omitted_shareability_hint_count,
            "shareability_hint_matches": to_jsonable(shareability_hint_matches),
            "artifact_disposition": DEFAULT_ARTIFACT_DISPOSITION,
            "git_safe": False,
        }
    def import_handoff_bundle(
        self,
        manifest: str | Path,
        *,
        dry_run: bool = False,
        replace: bool = False,
        include_drafts: bool = True,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
        drift_detail: TypingLiteral["summary", "exact"] = "summary",
    ) -> HandoffBundleImportRecord:
        manifest_path = _existing_path(manifest)
        source_label = str(manifest_path) if manifest_path is not None else "<string>"
        try:
            if manifest_path is not None:
                payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            else:
                payload = json.loads(str(manifest))
        except json.JSONDecodeError as exc:
            raise DoxaBaseError(
                "Could not parse handoff bundle manifest JSON from "
                f"{source_label}: {exc.msg} at line {exc.lineno} column {exc.colno}"
            ) from exc
        if not isinstance(payload, MappingABC):
            raise DoxaBaseError("Handoff bundle manifest must be a JSON object")
        if payload.get("format") != "doxabase.handoff_bundle.v1":
            raise DoxaBaseError(
                "Unsupported handoff bundle manifest format: "
                f"{payload.get('format')!r}"
            )
        if payload.get("recovery_complete") is not True:
            raise DoxaBaseError(
                "Handoff bundle manifest is not marked recovery_complete=true"
            )

        base_path = manifest_path.parent if manifest_path is not None else Path.cwd()
        trig_path = self._handoff_manifest_artifact_path(
            payload,
            "trig",
            base_path=base_path,
        )
        snapshot_path = self._handoff_manifest_artifact_path(
            payload,
            "revision_snapshots",
            base_path=base_path,
        )
        revision_iris = self._handoff_manifest_revision_iris(payload)
        graph_roles = self._handoff_manifest_graph_roles(payload, "trig")
        snapshot_graph_roles = self._handoff_manifest_graph_roles(
            payload,
            "revision_snapshots",
        )
        history_graphs = self._expand_graphs(["history"])
        pre_import_recovery_session_iris = self._recovery_session_iris(
            history_graphs
        )
        pre_import_snapshot_evidence = [
            self._revision_snapshot_evidence_status(revision_iri, history_graphs)
            for revision_iri in revision_iris
        ]
        warnings = self._handoff_manifest_import_warnings(
            payload,
            trig_path=trig_path,
            snapshot_path=snapshot_path,
        )
        invalid_handoff_validation_action = (
            self._import_handoff_bundle_validation_review_action(payload)
        )
        privacy_review_required_before_recovery = (
            self._handoff_manifest_sensitive_literal_count(payload) > 0
        )

        trig_imported: dict[str, int] = {}
        post_trig_snapshot_evidence: list[RevisionSnapshotEvidenceStatus] = []
        snapshot_import: RevisionSnapshotBundleImportRecord | None = None
        post_import_snapshot_evidence = pre_import_snapshot_evidence
        recovery_plan: StagedRevisionRecoveryPlan | None = None
        imported_recovery_session_iris: list[str] = []
        matching_recovery_session_iris: list[str] = []
        if dry_run:
            suggested_next_actions = [
                self._import_handoff_bundle_suggested_action(
                    manifest_path=source_label,
                    replace=replace,
                    include_drafts=include_drafts,
                    validation_scope=validation_scope,
                    drift_detail=drift_detail,
                    privacy_review_required_before_recovery=(
                        privacy_review_required_before_recovery
                    ),
                    validation_review_required_before_recovery=(
                        invalid_handoff_validation_action is not None
                        and not privacy_review_required_before_recovery
                    ),
                )
            ]
        else:
            trig_imported = self.import_trig(trig_path, replace=replace)
            post_trig_recovery_session_iris = self._recovery_session_iris(
                history_graphs
            )
            if replace and "history" in graph_roles:
                imported_recovery_session_iris = post_trig_recovery_session_iris
            else:
                imported_recovery_session_iris = [
                    session_iri
                    for session_iri in post_trig_recovery_session_iris
                    if session_iri not in pre_import_recovery_session_iris
                ]
            matching_recovery_session_iris = (
                self._matching_recovery_session_iris(
                    post_trig_recovery_session_iris,
                    revision_iris=revision_iris,
                    history_graphs=history_graphs,
                )
            )
            post_trig_snapshot_evidence = [
                self._revision_snapshot_evidence_status(
                    revision_iri,
                    history_graphs,
                )
                for revision_iri in revision_iris
            ]
            snapshot_import = self.import_revision_snapshots(
                snapshot_path,
                replace=replace,
            )
            post_import_snapshot_evidence = [
                self._revision_snapshot_evidence_status(
                    revision_iri,
                    history_graphs,
                )
                for revision_iri in revision_iris
            ]
            if revision_iris:
                recovery_plan = self.plan_staged_revision_recovery(
                    revision_iris,
                    current_staged_work_only=False,
                    include_drafts=include_drafts,
                    validation_scope=validation_scope,
                    drift_detail=drift_detail,
                )
            else:
                recovery_plan = self._empty_staged_revision_recovery_plan(
                    selection_mode="explicit_revision_iris",
                    requested_revision_iris=[],
                    current_staged_work_only=False,
                    include_drafts=include_drafts,
                    repair_draft_limit=1 if include_drafts else 0,
                    validation_scope=validation_scope,
                    drift_detail=drift_detail,
                    limit=50,
                    offset=0,
                    total_count=0,
                )
            recovery_plan = self._import_handoff_bundle_recovery_plan(
                recovery_plan,
                manifest_path=source_label if manifest_path is not None else None,
                snapshot_path=str(snapshot_path),
                revision_snapshots=snapshot_import,
            )
            recovery_session_actions = (
                self._import_handoff_bundle_recovery_session_actions(
                    matching_recovery_session_iris=matching_recovery_session_iris,
                    recovery_plan=recovery_plan,
                    manifest_path=(
                        source_label if manifest_path is not None else None
                    ),
                    include_drafts=include_drafts,
                    validation_scope=validation_scope,
                    drift_detail=drift_detail,
                )
            )
            recovery_suggested_next_actions = self._dedupe_suggested_next_actions(
                [
                    *recovery_session_actions,
                    *recovery_plan.suggested_next_actions,
                ]
            )
            if (
                matching_recovery_session_iris
                and recovery_plan.mutation_allowed_after
                != "handoff_preflight_required_before_mutation"
            ):
                recovery_plan = (
                    self._import_handoff_bundle_session_gated_recovery_plan(
                        recovery_plan,
                        recovery_session_actions,
                    )
                )
            if privacy_review_required_before_recovery:
                privacy_review_action = (
                    self._import_handoff_bundle_privacy_review_action(
                        graph_roles=graph_roles,
                        revision_iris=revision_iris,
                        snapshot_graph_roles=snapshot_graph_roles,
                        sensitive_literal_count=(
                            self._handoff_manifest_sensitive_literal_count(payload)
                        ),
                    )
                )
                recovery_plan = (
                    self._import_handoff_bundle_privacy_gated_recovery_plan(
                        recovery_plan,
                        privacy_review_action,
                    )
                )
                suggested_next_actions = [
                    action
                    for action in [
                        privacy_review_action,
                        invalid_handoff_validation_action,
                    ]
                    if action is not None
                ]
            elif invalid_handoff_validation_action is not None:
                recovery_plan = (
                    self._import_handoff_bundle_validation_gated_recovery_plan(
                        recovery_plan,
                        invalid_handoff_validation_action,
                    )
                )
                suggested_next_actions = [invalid_handoff_validation_action]
            elif (
                recovery_plan.mutation_allowed_after
                == "handoff_preflight_required_before_mutation"
                and recovery_plan.blocking_preflight_actions
            ):
                suggested_next_actions = self._dedupe_suggested_next_actions(
                    [
                        *(
                            [invalid_handoff_validation_action]
                            if invalid_handoff_validation_action is not None
                            else []
                        ),
                        *recovery_plan.blocking_preflight_actions,
                        *recovery_suggested_next_actions,
                    ]
                )
            else:
                suggested_next_actions = self._dedupe_suggested_next_actions(
                    [
                        *(
                            [invalid_handoff_validation_action]
                            if invalid_handoff_validation_action is not None
                            else []
                        ),
                        *recovery_suggested_next_actions,
                    ]
                )
            if not suggested_next_actions and not recovery_plan.processed_revision_iris:
                suggested_next_actions = [
                    self._post_handoff_import_project_brief_action()
                ]

        recovery_summary = self._handoff_bundle_recovery_summary(
            dry_run=dry_run,
            revision_iris=revision_iris,
            snapshot_evidence=post_import_snapshot_evidence,
            trig_total_imported=sum(trig_imported.values()),
            revision_snapshots=snapshot_import,
            imported_recovery_session_iris=imported_recovery_session_iris,
            matching_recovery_session_iris=matching_recovery_session_iris,
            recovery_plan=recovery_plan,
            suggested_next_actions=suggested_next_actions,
            privacy_review_required_before_recovery=(
                privacy_review_required_before_recovery
            ),
            validation_review_required_before_recovery=(
                invalid_handoff_validation_action is not None
                and not privacy_review_required_before_recovery
            ),
        )

        return HandoffBundleImportRecord(
            path=source_label,
            format=str(payload["format"]),
            dry_run=dry_run,
            replace=replace,
            manifest=dict(payload),
            paths={
                "trig": str(trig_path),
                "revision_snapshots": str(snapshot_path),
                **({"manifest": source_label} if manifest_path is not None else {}),
            },
            graph_roles=graph_roles,
            snapshot_graph_roles=snapshot_graph_roles,
            revision_iris=revision_iris,
            pre_import_snapshot_evidence=pre_import_snapshot_evidence,
            trig_imported=trig_imported,
            trig_total_imported=sum(trig_imported.values()),
            post_trig_snapshot_evidence=post_trig_snapshot_evidence,
            revision_snapshots=snapshot_import,
            post_import_snapshot_evidence=post_import_snapshot_evidence,
            recovery_plan=recovery_plan,
            imported_recovery_session_iris=imported_recovery_session_iris,
            matching_recovery_session_iris=matching_recovery_session_iris,
            recovery_summary=recovery_summary,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions if action.call
            ],
            warnings=warnings,
        )
    @staticmethod
    def _is_placeholder_snapshot_import_action(
        action: SuggestedNextAction,
    ) -> bool:
        return (
            action.tool_name == "import_revision_snapshots"
            and action.arguments.get("path_is_placeholder") is True
        )
    @staticmethod
    def _import_handoff_bundle_missing_resolved_snapshots(
        recovery_plan: StagedRevisionRecoveryPlan,
        *,
        bundled_snapshot_revision_iris: list[str],
    ) -> list[RevisionSnapshotEvidenceStatus]:
        bundled = set(bundled_snapshot_revision_iris)
        missing_by_iri: dict[str, RevisionSnapshotEvidenceStatus] = {}
        for lane in recovery_plan.lanes:
            for evidence in (
                lane.source_snapshot_evidence,
                lane.current_snapshot_evidence,
            ):
                if evidence.revision_iri in bundled:
                    continue
                if evidence.status == "history_plus_snapshot_rows":
                    continue
                missing_by_iri.setdefault(evidence.revision_iri, evidence)
        return list(missing_by_iri.values())
    def _import_handoff_bundle_broader_snapshot_action(
        self,
        missing_evidence: list[RevisionSnapshotEvidenceStatus],
        *,
        manifest_path: str | None,
        snapshot_path: str,
        revision_snapshots: RevisionSnapshotBundleImportRecord,
    ) -> SuggestedNextAction:
        missing_revision_iris = [evidence.revision_iri for evidence in missing_evidence]
        missing_graph_roles = list(
            dict.fromkeys(
                graph_role
                for evidence in missing_evidence
                for graph_role in (
                    evidence.missing_snapshot_row_graph_roles
                    or evidence.rdf_snapshot_graph_roles
                    or evidence.exact_snapshot_graph_roles
                )
            )
        )
        arguments: dict[str, Any] = {
            "path": "<broader-source-revision-snapshots.json>",
            "path_is_placeholder": True,
            "missing_revision_iris": missing_revision_iris,
            "already_imported_snapshot_path": snapshot_path,
        }
        if manifest_path is not None:
            arguments["handoff_manifest_path"] = manifest_path
        if missing_graph_roles:
            arguments["missing_graph_roles"] = missing_graph_roles
        imported_text = (
            f"imported {revision_snapshots.imported_snapshot_count}, "
            f"skipped {revision_snapshots.skipped_snapshot_count}"
        )
        reason = (
            "The paired handoff snapshot artifact has already been imported "
            f"({imported_text}) from '{snapshot_path}', but it does not contain "
            "complete snapshot rows for resolved recovery target revision(s): "
            f"{', '.join(missing_revision_iris)}. Re-importing the current "
            "manifest's snapshot JSON will not clear this gate; request or "
            "create a broader source-side revision snapshot bundle containing "
            "those revision_iris, then import that broader JSON here before "
            "mutating recovered staged work."
        )
        if missing_graph_roles:
            reason += (
                " Missing graph role(s): "
                f"{', '.join(missing_graph_roles)}."
            )
        return SuggestedNextAction(
            action_label="Import broader source snapshot bundle",
            tool_name="import_revision_snapshots",
            mcp_tool_name="doxabase.import_revision_snapshots",
            arguments=arguments,
            reason=reason,
            call=self._suggested_call_string(
                "import_revision_snapshots",
                arguments,
            ),
        )
    def _handoff_manifest_artifact_path(
        self,
        manifest: MappingABC[str, Any],
        artifact_key: str,
        *,
        base_path: Path,
    ) -> Path:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, MappingABC):
            raise DoxaBaseError("Handoff bundle manifest must contain artifacts")
        artifact = artifacts.get(artifact_key)
        if not isinstance(artifact, MappingABC):
            raise DoxaBaseError(
                f"Handoff bundle manifest is missing artifacts.{artifact_key}"
            )
        path_value = artifact.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            raise DoxaBaseError(
                f"Handoff bundle manifest artifacts.{artifact_key}.path "
                "must be a non-empty string"
            )
        path = Path(path_value)
        if not path.is_absolute():
            path = base_path / path
        if path.exists():
            return path
        sibling_path = base_path / path.name
        if sibling_path != path and sibling_path.exists():
            return sibling_path
        raise DoxaBaseError(
            "Handoff bundle artifact path does not exist: "
            f"{path}. Check the manifest path or move the paired artifacts "
            "next to the manifest."
        )
    @staticmethod
    def _handoff_manifest_revision_iris(
        manifest: MappingABC[str, Any],
    ) -> list[str]:
        revision_iris = manifest.get("revision_iris")
        if not isinstance(revision_iris, list):
            raise DoxaBaseError(
                "Handoff bundle manifest must contain revision_iris list"
            )
        values: list[str] = []
        for value in revision_iris:
            if not isinstance(value, str) or not value.strip():
                raise DoxaBaseError(
                    "Handoff bundle manifest revision_iris entries must be strings"
                )
            if value not in values:
                values.append(value)
        return values
    @staticmethod
    def _handoff_manifest_graph_roles(
        manifest: MappingABC[str, Any],
        artifact_key: str,
    ) -> list[str]:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, MappingABC):
            return []
        artifact = artifacts.get(artifact_key)
        if not isinstance(artifact, MappingABC):
            return []
        graph_roles = artifact.get("graph_roles")
        if not isinstance(graph_roles, list):
            return []
        return [value for value in graph_roles if isinstance(value, str)]
    @staticmethod
    def _handoff_manifest_import_warnings(
        manifest: MappingABC[str, Any],
        *,
        trig_path: Path,
        snapshot_path: Path,
    ) -> list[str]:
        warnings: list[str] = []
        sensitive_literal_count = manifest.get("sensitive_literal_count")
        if isinstance(sensitive_literal_count, int) and sensitive_literal_count > 0:
            warnings.append(
                "Handoff bundle manifest records potential sensitive terms in "
                "the exported artifacts. Import may still be useful locally, but "
                "do not share the artifacts until privacy review is complete."
            )
        shareability_review_required = manifest.get("shareability_review_required")
        shareability_review_status = manifest.get("shareability_review_status")
        if (
            shareability_review_required is True
            and shareability_review_status == "required_not_completed"
        ):
            warnings.append(
                "Handoff bundle manifest is scanner-clean only unless "
                "sensitive_literal_count is nonzero; shareability review is "
                "still required before sharing artifacts beyond the intended "
                "receiver."
            )
        if trig_path == snapshot_path:
            warnings.append(
                "Handoff bundle manifest points TriG and snapshot artifacts to "
                "the same path; import is likely to fail unless the manifest is "
                "repaired."
            )
        invalid_scope = DoxaBase._handoff_manifest_invalid_validation_scope(manifest)
        if invalid_scope is not None:
            result_count = manifest.get("validation_result_count")
            result_text = (
                f" with {result_count} SHACL result(s)"
                if isinstance(result_count, int) and result_count > 0
                else ""
            )
            warnings.append(
                "Handoff bundle manifest records a failed export validation "
                f"for scope {invalid_scope!r}{result_text}. Import is faithful "
                "for local diagnostics, but run validate_graph on the receiver "
                "before following recovery or mutation actions."
            )
        return warnings
    @staticmethod
    def _handoff_manifest_sensitive_literal_count(
        manifest: MappingABC[str, Any],
    ) -> int:
        sensitive_literal_count = manifest.get("sensitive_literal_count")
        if isinstance(sensitive_literal_count, int) and sensitive_literal_count > 0:
            return sensitive_literal_count
        return 0
    @staticmethod
    def _handoff_manifest_invalid_validation_scope(
        manifest: MappingABC[str, Any],
    ) -> str | None:
        candidate: MappingABC[str, Any] = manifest
        if (
            candidate.get("would_block_invalid_export") is not True
            and candidate.get("validation_conforms") is not False
        ):
            artifacts = manifest.get("artifacts")
            if isinstance(artifacts, MappingABC):
                trig_artifact = artifacts.get("trig")
                if isinstance(trig_artifact, MappingABC):
                    candidate = trig_artifact
        if (
            candidate.get("would_block_invalid_export") is not True
            and candidate.get("validation_conforms") is not False
        ):
            return None
        scope = candidate.get("validation_scope") or manifest.get("validation_scope")
        if isinstance(scope, str) and scope in {
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        }:
            return scope
        return "all"
    def _import_handoff_bundle_validation_review_action(
        self,
        manifest: MappingABC[str, Any],
    ) -> EffectAnnotatedSuggestedNextAction | None:
        validation_scope = self._handoff_manifest_invalid_validation_scope(manifest)
        if validation_scope is None:
            return None
        result_count = manifest.get("validation_result_count")
        limit_results = 20
        if isinstance(result_count, int):
            limit_results = max(20, min(result_count, 100))
        arguments: dict[str, Any] = {
            "scope": validation_scope,
            "limit_results": limit_results,
        }
        return self._effect_annotated_suggested_next_action(
            action_label="Inspect imported handoff validation failures",
            tool_name="validate_graph",
            arguments=arguments,
            reason=(
                "The imported handoff manifest records that export validation "
                "failed for this graph scope. Inspect receiver-side SHACL "
                "diagnostics before following recovery or mutation actions."
            ),
        )
    def _import_handoff_bundle_privacy_review_action(
        self,
        *,
        graph_roles: list[str],
        revision_iris: list[str],
        snapshot_graph_roles: list[str],
        sensitive_literal_count: int,
    ) -> EffectAnnotatedSuggestedNextAction:
        arguments: dict[str, Any] = {
            "export_kind": "handoff_bundle",
            "graphs": graph_roles or ["project"],
            "limit": max(20, min(sensitive_literal_count, 100)),
        }
        if revision_iris:
            arguments["revision_iris"] = revision_iris
        if snapshot_graph_roles:
            arguments["snapshot_graph_roles"] = snapshot_graph_roles
        return self._effect_annotated_suggested_next_action(
            action_label="Review imported handoff privacy",
            tool_name="export_preflight",
            arguments=arguments,
            reason=(
                "The imported handoff manifest records sensitive-looking "
                "artifact terms. Run this redacted receiver-side preflight "
                "before following staged recovery or mutation actions."
            ),
        )
    def _import_handoff_bundle_suggested_action(
        self,
        *,
        manifest_path: str,
        replace: bool,
        include_drafts: bool,
        validation_scope: str | None,
        drift_detail: str,
        privacy_review_required_before_recovery: bool = False,
        validation_review_required_before_recovery: bool = False,
    ) -> SuggestedNextAction:
        arguments: dict[str, Any] = {
            "manifest_path": manifest_path,
            "dry_run": False,
            "replace": replace,
            "include_drafts": include_drafts,
            "drift_detail": drift_detail,
        }
        if validation_scope is not None:
            arguments["validation_scope"] = validation_scope
        if privacy_review_required_before_recovery:
            action_label = "Import privacy-gated handoff bundle"
            reason = (
                "Dry-run parsed a recovery-complete handoff manifest that "
                "records sensitive-looking artifact terms. The dry-run is the "
                "non-mutating manifest privacy gate; run the real import only "
                "for local recovery, then follow its redacted export_preflight "
                "gate before any recovery or mutation actions."
            )
        elif validation_review_required_before_recovery:
            action_label = "Import validation-gated handoff bundle"
            reason = (
                "Dry-run parsed a recovery-complete handoff manifest that "
                "records failed export validation. The dry-run is the "
                "non-mutating validation gate; run the real import only for "
                "local diagnostics, then follow its validate_graph gate before "
                "any recovery or mutation actions."
            )
        else:
            action_label = "Import handoff bundle"
            reason = (
                "Dry-run parsed a recovery-complete handoff manifest. Run the "
                "real import to load project/history RDF first, then companion "
                "revision snapshot rows, and return a staged recovery plan."
            )
        return SuggestedNextAction(
            action_label=action_label,
            tool_name="import_handoff_bundle",
            mcp_tool_name="doxabase.import_handoff_bundle",
            arguments=arguments,
            reason=reason,
            call=self._suggested_call_string("import_handoff_bundle", arguments),
        )
    @staticmethod
    def _preflight_handoff_bundle_export_paths(
        trig_path: str | Path,
        revision_snapshot_path: str | Path,
        manifest_path: str | Path | None = None,
        *,
        overwrite: bool,
    ) -> None:
        paths = [Path(trig_path), Path(revision_snapshot_path)]
        if manifest_path is not None:
            paths.append(Path(manifest_path))
        resolved_paths = [path.resolve(strict=False) for path in paths]
        if len(set(resolved_paths)) != len(resolved_paths):
            raise DoxaBaseError(
                "export_handoff_bundle requires distinct trig_path, "
                "revision_snapshot_path, and manifest_path outputs."
            )
        if overwrite:
            return
        existing = [str(path) for path in paths if path.exists()]
        if existing:
            raise DoxaBaseError(
                "Export path already exists: "
                f"{existing[0]}. Use overwrite=True to replace it."
            )
    def _export_preflight_graph_matches(
        self,
        matches: list[SensitiveLiteralMatch],
    ) -> list[ExportPreflightMatch]:
        return [
            ExportPreflightMatch(
                export_part="graphs",
                match_id=self._export_preflight_match_id(
                    export_part="graphs",
                    graph=match.graph,
                    subject=match.subject,
                    predicate=match.predicate,
                    object_kind=match.object_kind,
                    term_position=match.term_position,
                    term_kind=match.term_kind,
                    match_kind=match.match_kind,
                    redacted_snippet=match.redacted_snippet,
                    revision_iri=None,
                ),
                graph=match.graph,
                subject=match.subject,
                predicate=match.predicate,
                object_kind=match.object_kind,
                term_position=match.term_position,
                term_kind=match.term_kind,
                match_kind=match.match_kind,
                redacted_snippet=match.redacted_snippet,
            )
            for match in matches
        ]
    @staticmethod
    def _export_preflight_match_id(
        *,
        export_part: str,
        graph: str,
        subject: str,
        predicate: str,
        object_kind: str,
        term_position: str,
        term_kind: str,
        match_kind: str,
        redacted_snippet: str,
        revision_iri: str | None,
    ) -> str:
        digest = hashlib.sha256()
        for value in (
            export_part,
            graph,
            subject,
            predicate,
            object_kind,
            term_position,
            term_kind,
            match_kind,
            redacted_snippet,
            revision_iri or "",
        ):
            digest.update(value.encode("utf-8"))
            digest.update(b"\x1f")
        return f"redacted-sha256:{digest.hexdigest()}"
    def _export_preflight_suggested_actions(
        self,
        record: ExportPreflightRecord,
    ) -> list[SuggestedNextAction]:
        if record.decision == "block":
            actions: list[SuggestedNextAction] = []
            if record.would_block_invalid_export and record.validation_scope:
                arguments = {
                    "scope": record.validation_scope,
                    "limit_results": max(record.limit, 20),
                }
                actions.append(
                    SuggestedNextAction(
                        action_label="Inspect export validation failures",
                        tool_name="validate_graph",
                        mcp_tool_name="doxabase.validate_graph",
                        arguments=arguments,
                        reason=(
                            "The live graph validation gate failed for this "
                            "export scope. Inspect SHACL diagnostics and repair "
                            "the graph before writing a recovery or share artifact."
                        ),
                        call=self._suggested_call_string(
                            "validate_graph",
                            arguments,
                        ),
                    )
                )
            if record.graph_sensitive_literal_count and record.graphs:
                arguments: dict[str, Any] = {
                    "graphs": record.graphs,
                    "limit": max(record.limit, 20),
                }
                actions.append(
                    SuggestedNextAction(
                        action_label="Inspect graph privacy matches",
                        tool_name="scan_sensitive_literals",
                        mcp_tool_name="doxabase.scan_sensitive_literals",
                        arguments=arguments,
                        reason=(
                            "Review redacted graph-term matches before changing "
                            "scope or removing sensitive-looking graph content."
                        ),
                        call=self._suggested_call_string(
                            "scan_sensitive_literals",
                            arguments,
                        ),
                    )
                )
            if record.snapshot_sensitive_literal_count:
                arguments = {
                    "export_kind": "revision_snapshots",
                    "revision_iris": record.revision_iris,
                    "snapshot_graph_roles": record.snapshot_graph_roles,
                    "limit": max(record.limit, 20),
                }
                actions.append(
                    SuggestedNextAction(
                        action_label="Review snapshot privacy matches",
                        tool_name="export_preflight",
                        mcp_tool_name="doxabase.export_preflight",
                        arguments=arguments,
                        reason=(
                            "Stored revision snapshots can contain historical "
                            "terms outside current graph content; use the "
                            "snapshot-only preflight matches when narrowing or "
                            "cleaning the handoff scope."
                        ),
                        call=self._suggested_call_string(
                            "export_preflight",
                            arguments,
                        ),
                    )
                )
            if record.graph_sensitive_literal_count and record.graphs:
                arguments = {
                    "seed_iris": ["<target-resource-iri>"],
                    "profile": "dataset_brief",
                    "max_triples": 500,
                    "limit": max(record.limit, 20),
                }
                actions.append(
                    TemplatedSuggestedNextAction(
                        action_label="Preflight resource-scoped context slice",
                        tool_name="preflight_context_slice_export",
                        mcp_tool_name="doxabase.preflight_context_slice_export",
                        arguments=arguments,
                        reason=(
                            "If the intended handoff only needs clean context "
                            "around known resources, preflight a context-slice "
                            "export instead of weakening fail_on_sensitive on "
                            "the blocked broader export. Context-slice exports "
                            "are importable review context, not recovery-complete "
                            "revision handoffs."
                        ),
                        call=self._suggested_call_string(
                            "preflight_context_slice_export",
                            arguments,
                        ),
                        required_extra_arguments=["seed_iris"],
                        placeholder_fields=["seed_iris"],
                        reviewed_value_fields=["seed_iris"],
                    )
                )
            return actions

        if record.export_kind == "graph":
            arguments = {
                "path": "<review-artifact.ttl>",
                "graphs": record.graphs,
                "fail_on_sensitive": True,
                "fail_on_invalid": True,
            }
            if record.validation_scope is not None:
                arguments["validation_scope"] = record.validation_scope
            tool_name = "export_graph"
            action_label = "Export graph artifact"
            reason = (
                "The selected graph terms scanned clean; keep "
                "fail_on_sensitive=True and fail_on_invalid=True so the write "
                "still blocks if content changes before export."
            )
        elif record.export_kind == "trig":
            arguments = {
                "path": "<project-review-bundle.trig>",
                "graphs": record.graphs,
                "fail_on_sensitive": True,
                "fail_on_invalid": True,
            }
            if record.validation_scope is not None:
                arguments["validation_scope"] = record.validation_scope
            tool_name = "export_trig"
            action_label = "Export TriG bundle"
            reason = (
                "The selected named graphs scanned clean; keep "
                "fail_on_sensitive=True and fail_on_invalid=True so the write "
                "still blocks if content changes before export."
            )
        elif record.export_kind == "revision_snapshots":
            arguments = {
                "path": "<revision-snapshots.json>",
                "fail_on_sensitive": True,
            }
            if record.revision_iris:
                arguments["revision_iris"] = record.revision_iris
            if record.snapshot_graph_roles:
                arguments["graph_roles"] = record.snapshot_graph_roles
            tool_name = "export_revision_snapshots"
            action_label = "Export revision snapshots"
            reason = (
                "The selected snapshot rows scanned clean; keep "
                "fail_on_sensitive=True so the write still blocks if snapshot "
                "content changes before export."
            )
        else:
            arguments = {
                "trig_path": "<project-handoff.trig>",
                "revision_snapshot_path": "<revision-snapshots.json>",
                "manifest_path": "<handoff-manifest.json>",
                "graphs": record.graphs,
                "fail_on_sensitive": True,
                "fail_on_invalid": True,
            }
            if record.validation_scope is not None:
                arguments["validation_scope"] = record.validation_scope
            if record.revision_iris:
                arguments["revision_iris"] = record.revision_iris
            if record.snapshot_graph_roles:
                arguments["snapshot_graph_roles"] = record.snapshot_graph_roles
            tool_name = "export_handoff_bundle"
            action_label = "Export handoff bundle"
            reason = (
                "The selected RDF graphs and snapshot rows scanned clean; keep "
                "fail_on_sensitive=True and fail_on_invalid=True so the paired "
                "write still blocks if content changes before export."
            )

        action_class = SuggestedNextAction
        action_kwargs: dict[str, Any] = {}
        if (
            record.export_kind == "handoff_bundle"
            and tool_name == "export_handoff_bundle"
        ):
            placeholder_fields = [
                "trig_path",
                "revision_snapshot_path",
                "manifest_path",
            ]
            action_class = TemplatedSuggestedNextAction
            action_kwargs = {
                "required_extra_arguments": placeholder_fields,
                "placeholder_fields": placeholder_fields,
                "reviewed_value_fields": placeholder_fields,
            }

        return [
            action_class(
                action_label=action_label,
                tool_name=tool_name,
                mcp_tool_name=f"doxabase.{tool_name}",
                arguments=arguments,
                reason=reason,
                call=self._suggested_call_string(tool_name, arguments),
                **action_kwargs,
            )
        ]
    def _revision_snapshot_export_privacy_warnings(
        self,
        entries: list[dict[str, Any]],
        *,
        limit: int = 5,
    ) -> tuple[int, list[str]]:
        examples: list[str] = []
        omitted = 0
        match_count = 0
        for entry in entries:
            graph_role = str(entry["graph_role"])
            revision_iri = str(entry["revision_iri"])
            for quad in entry["quads"]:
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
                    predicate = self._redact_sensitive_context_value(
                        str(quad["predicate"])
                    )
                    predicate_label = self._compact_iri(predicate) or predicate
                    match_count += 1
                    if len(examples) < limit:
                        examples.append(
                            (
                                f"{graph_role} {term_position} "
                                f"{predicate_label} "
                                f"{redacted_snippet} in snapshot for {revision_iri}"
                            )
                        )
                    else:
                        omitted += 1

        if match_count == 0:
            return 0, []
        warning = (
            f"Revision snapshot export includes {match_count} potential sensitive "
            "term match(es). Snapshot JSON faithfully preserves stored graph "
            "content; run scan_sensitive_literals on project graph roles before "
            "sharing. Redacted examples: "
            + "; ".join(examples)
        )
        if omitted:
            warning += f" ({omitted} additional match(es) omitted.)"
        return match_count, [warning]
    def _snapshot_export_revision_iris(self, revision_iris: list[str]) -> list[str]:
        if not revision_iris:
            return []
        history_graphs = self._expand_graphs(["history"])
        expanded: list[str] = []
        for revision_iri in revision_iris:
            if revision_iri not in expanded:
                expanded.append(revision_iri)
            staged_source_iri = self._first_object(
                history_graphs,
                revision_iri,
                "rc:appliesStagedRevision",
            )
            if staged_source_iri is not None and staged_source_iri not in expanded:
                expanded.append(staged_source_iri)
        return expanded
    def import_revision_snapshots(
        self,
        source: str | Path,
        *,
        replace: bool = False,
    ) -> RevisionSnapshotBundleImportRecord:
        path = _existing_path(source)
        source_label = str(path) if path is not None else "<string>"
        try:
            if path is not None:
                payload = json.loads(path.read_text(encoding="utf-8"))
            else:
                payload = json.loads(str(source))
        except json.JSONDecodeError as exc:
            raise DoxaBaseError(
                "Could not parse revision snapshot bundle JSON from "
                f"{source_label}: {exc.msg} at line {exc.lineno} column {exc.colno}"
            ) from exc
        if not isinstance(payload, MappingABC):
            raise DoxaBaseError("Revision snapshot bundle must be a JSON object")
        format_value = payload.get("format")
        if format_value != "doxabase.revision_snapshot_bundle.v1":
            raise DoxaBaseError(
                "Unsupported revision snapshot bundle format: "
                f"{format_value!r}"
            )
        snapshots = payload.get("snapshots")
        if not isinstance(snapshots, list):
            raise DoxaBaseError("Revision snapshot bundle must contain snapshots list")

        normalized_snapshots = [
            self._normalize_snapshot_bundle_entry(raw_snapshot, index=index)
            for index, raw_snapshot in enumerate(snapshots, start=1)
        ]

        imported_snapshot_count = 0
        skipped_snapshot_count = 0
        imported_quad_count = 0
        revision_iris: list[str] = []
        graph_roles: list[str] = []
        for snapshot in normalized_snapshots:
            revision_iri = snapshot["revision_iri"]
            graph_role = snapshot["graph_role"]
            revision_iris.append(revision_iri)
            graph_roles.append(graph_role)
            if (
                not replace
                and self._graph_snapshot_storage_exists(revision_iri, graph_role)
            ):
                skipped_snapshot_count += 1
                continue
            self._insert_graph_snapshot_bundle_entry(snapshot, replace=replace)
            imported_snapshot_count += 1
            imported_quad_count += len(snapshot["quads"])
        self._conn.commit()
        unique_revision_iris = list(dict.fromkeys(revision_iris))
        history_graphs = self._expand_graphs(["history"])
        post_import_snapshot_evidence = [
            self._revision_snapshot_evidence_status(
                revision_iri,
                history_graphs,
            )
            for revision_iri in unique_revision_iris
        ]
        return RevisionSnapshotBundleImportRecord(
            path=source_label,
            format=format_value,
            replace=replace,
            revision_iris=unique_revision_iris,
            graph_roles=list(dict.fromkeys(graph_roles)),
            snapshot_count=len(snapshots),
            imported_snapshot_count=imported_snapshot_count,
            skipped_snapshot_count=skipped_snapshot_count,
            quad_count=sum(len(snapshot["quads"]) for snapshot in normalized_snapshots),
            imported_quad_count=imported_quad_count,
            post_import_snapshot_evidence=post_import_snapshot_evidence,
        )
    def export_graph(
        self,
        path: str | Path,
        *,
        graphs: Iterable[str] | str | None = "map",
        format: str = "turtle",
        overwrite: bool = False,
        fail_on_sensitive: bool = False,
        fail_on_invalid: bool = True,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> GraphExportRecord:
        graph_names = self._graph_names_for_export(graphs)
        sensitive_literal_count, privacy_warnings = self._export_privacy_warnings(
            graph_names
        )
        shareability_hints = self._shareability_hints_for_graphs(graph_names)
        shareability_hint_count, shareability_hint_matches = (
            self._shareability_hint_matches_for_graphs(graph_names)
        )
        validation = self._export_validation_result(
            graph_names,
            validation_scope=validation_scope,
            default_scope=None,
        )
        validation_warnings = self._export_validation_warnings(validation)
        validation_blocks_export = validation is not None and not validation.conforms
        self._raise_if_sensitive_export_blocked(
            fail_on_sensitive=fail_on_sensitive,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
        )
        self._raise_if_invalid_export_blocked(
            fail_on_invalid=fail_on_invalid,
            validation=validation,
        )
        rdf_graph = self._to_graph_roles(graph_names)
        data = rdf_graph.serialize(format=format)
        bytes_written = self._write_export(path, data, overwrite=overwrite)
        return GraphExportRecord(
            path=str(path),
            format=format,
            graphs=graph_names,
            graph_counts=self._graph_counts(graph_names),
            triples=len(rdf_graph),
            bytes_written=bytes_written,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
            warnings=[
                *privacy_warnings,
                *validation_warnings,
                *self._shareability_hint_warnings(shareability_hints),
            ],
            validation_scope=validation.scope if validation is not None else None,
            validation_conforms=(
                validation.conforms if validation is not None else None
            ),
            validation_result_count=(
                validation.result_count if validation is not None else 0
            ),
            validation_results=validation.results if validation is not None else [],
            would_block_invalid_export=validation_blocks_export,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
        )
    def export_trig(
        self,
        path: str | Path,
        *,
        graphs: Iterable[str] | str | None = None,
        overwrite: bool = False,
        graph_iri_prefix: str = RCG_PREFIX,
        fail_on_sensitive: bool = False,
        fail_on_invalid: bool = True,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ]
        | None = None,
    ) -> GraphExportRecord:
        graph_names = self._graph_names_for_export(graphs, default_preset="project")
        sensitive_literal_count, privacy_warnings = self._export_privacy_warnings(
            graph_names
        )
        shareability_hints = self._shareability_hints_for_graphs(graph_names)
        shareability_hint_count, shareability_hint_matches = (
            self._shareability_hint_matches_for_graphs(graph_names)
        )
        validation = self._export_validation_result(
            graph_names,
            validation_scope=validation_scope,
            default_scope="all",
        )
        validation_warnings = self._export_validation_warnings(validation)
        validation_blocks_export = validation is not None and not validation.conforms
        export_scope_warnings = self._export_scope_warnings(
            export_kind="trig",
            graph_names=graph_names,
        )
        self._raise_if_sensitive_export_blocked(
            fail_on_sensitive=fail_on_sensitive,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
        )
        self._raise_if_invalid_export_blocked(
            fail_on_invalid=fail_on_invalid,
            validation=validation,
        )
        dataset = self.to_dataset(graph_names, graph_iri_prefix=graph_iri_prefix)
        data = dataset.serialize(format="trig")
        bytes_written = self._write_export(path, data, overwrite=overwrite)
        return GraphExportRecord(
            path=str(path),
            format="trig",
            graphs=graph_names,
            graph_counts=self._graph_counts(graph_names),
            triples=len(dataset),
            bytes_written=bytes_written,
            sensitive_literal_count=sensitive_literal_count,
            privacy_warnings=privacy_warnings,
            warnings=[
                *privacy_warnings,
                *validation_warnings,
                *self._shareability_hint_warnings(shareability_hints),
                *export_scope_warnings,
            ],
            validation_scope=validation.scope if validation is not None else None,
            validation_conforms=(
                validation.conforms if validation is not None else None
            ),
            validation_result_count=(
                validation.result_count if validation is not None else 0
            ),
            validation_results=validation.results if validation is not None else [],
            would_block_invalid_export=validation_blocks_export,
            artifact_kind=self._trig_export_artifact_kind(graph_names),
            recommended_import_tool="doxabase.import_trig",
            recovery_complete=False,
            shareability_hints=shareability_hints,
            shareability_hint_count=shareability_hint_count,
            returned_shareability_hint_count=len(shareability_hint_matches),
            omitted_shareability_hint_count=max(
                0,
                shareability_hint_count - len(shareability_hint_matches),
            ),
            shareability_hint_matches=shareability_hint_matches,
        )
    def _export_privacy_warnings(
        self,
        graph_names: list[str],
    ) -> tuple[int, list[str]]:
        scan = self.scan_sensitive_literals(graph_names, limit=5)
        if scan.match_count == 0:
            return 0, []
        example_text = "; ".join(
            (
                f"{match.graph} {match.term_position} "
                f"{self._compact_iri(match.predicate) or match.predicate} "
                f"{match.redacted_snippet}"
            )
            for match in scan.matches[:3]
        )
        warning = (
            f"Export includes {scan.match_count} potential sensitive graph term "
            "match(es). Run scan_sensitive_literals on these graph roles before "
            "sharing. Redacted examples: "
            f"{example_text}"
        )
        if scan.omitted_match_count:
            warning += f" ({scan.omitted_match_count} additional match(es) omitted.)"
        return scan.match_count, [warning]
    @staticmethod
    def _raise_if_sensitive_export_blocked(
        *,
        fail_on_sensitive: bool,
        sensitive_literal_count: int,
        privacy_warnings: list[str],
    ) -> None:
        if not fail_on_sensitive or sensitive_literal_count == 0:
            return
        warning_text = " ".join(privacy_warnings) if privacy_warnings else (
            "Potential sensitive graph terms detected."
        )
        raise DoxaBaseError(
            "Export blocked because fail_on_sensitive=True and the selected "
            f"graph roles contain {sensitive_literal_count} potential sensitive "
            f"graph term match(es). {warning_text}"
        )
    @staticmethod
    def _raise_if_markdown_sensitive_export_blocked(
        *,
        fail_on_sensitive: bool,
        sensitive_literal_count: int,
        privacy_warnings: list[str],
    ) -> None:
        if not fail_on_sensitive or sensitive_literal_count == 0:
            return
        warning_text = " ".join(privacy_warnings) if privacy_warnings else (
            "Potential sensitive literals detected."
        )
        raise DoxaBaseError(
            "Markdown export blocked because fail_on_sensitive=True and the "
            f"generated review bundle contains {sensitive_literal_count} "
            f"potential sensitive literal match(es). {warning_text}"
        )
    def _markdown_export_privacy_warnings(
        self,
        data: str,
        *,
        limit: int = 5,
        final_privacy_warning_line_numbers: bool = False,
    ) -> tuple[int, list[str]]:
        match_count = 0
        omitted_match_count = 0
        examples: list[str] = []
        lines = data.splitlines()
        insertion_after_line = (
            2
            if final_privacy_warning_line_numbers
            and len(lines) >= 2
            and lines[0].startswith("# ")
            and lines[1] == ""
            else 0
        )
        inserted_line_count = 4 if final_privacy_warning_line_numbers else 0
        for line_number, line in enumerate(lines, start=1):
            match_kind, redacted_snippet = self._sensitive_literal_match(line)
            if match_kind is None or redacted_snippet is None:
                continue
            match_count += 1
            if len(examples) < limit:
                final_line_number = (
                    line_number + inserted_line_count
                    if line_number > insertion_after_line
                    else line_number
                )
                examples.append(f"line {final_line_number} {redacted_snippet}")
            else:
                omitted_match_count += 1
        if match_count == 0:
            return 0, []
        example_text = "; ".join(examples)
        warning = (
            f"Markdown export includes {match_count} potential sensitive literal "
            "match(es). Review the generated file before sharing; staged patch "
            "content is preserved and not redacted. Redacted examples: "
            f"{example_text}"
        )
        if omitted_match_count:
            warning += f" ({omitted_match_count} additional match(es) omitted.)"
        return match_count, [warning]
    def _graph_names_for_export(
        self,
        graphs: Iterable[str] | str | None,
        *,
        default_preset: str | None = None,
    ) -> list[str]:
        requested_graphs = self._requested_graphs(graphs)
        if requested_graphs is None and default_preset is not None:
            requested_graphs = [default_preset]
        graph_names: list[str] = []
        for graph in requested_graphs or []:
            if graph is None:
                continue
            if graph == "all":
                graph_names.extend(self._graph_names_for_export("all_with_seeds"))
                continue
            preset = EXPORT_PRESETS.get(graph)
            if preset is not None:
                graph_names.extend(preset)
            else:
                graph_names.append(graph)
        graph_names = list(dict.fromkeys(graph_names))
        if not graph_names:
            raise DoxaBaseError("graphs must contain at least one graph role")
        known_graphs = {
            row["name"] for row in self._conn.execute("SELECT name FROM named_graphs")
        }
        unknown_graphs = [graph for graph in graph_names if graph not in known_graphs]
        if unknown_graphs:
            raise DoxaBaseError(
                f"Unknown graph role(s): {', '.join(sorted(unknown_graphs))}"
            )
        return graph_names
    def _export_graph_identifier(self, graph: str, graph_iri_prefix: str) -> str:
        if "://" in graph or graph.startswith("urn:"):
            return graph
        return f"{graph_iri_prefix}{graph}"
    def _write_export(
        self,
        path: str | Path,
        data: str,
        *,
        overwrite: bool,
    ) -> int:
        output_path = Path(path)
        if output_path.exists() and not overwrite:
            raise DoxaBaseError(
                f"Export path already exists: {output_path}. Use overwrite=True to replace it."
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(data, encoding="utf-8")
        return len(data.encode("utf-8"))
