"""Query repair staging and staged patch payload search.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via StagingRepairsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class StagingRepairsMixin:
    def search_staged_patch_payloads(
        self,
        query: str,
        *,
        graph: str | None = "history",
        current_staged_work_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> StagedPatchPayloadSearchResults:
        if not query.strip():
            raise DoxaBaseError("Search query must not be empty")
        if limit < 1:
            raise DoxaBaseError("Search limit must be at least 1")
        if offset < 0:
            raise DoxaBaseError("Search offset must be non-negative")

        search_tokens = _search_tokens(query)
        fts_query = _fts_query_from_tokens(search_tokens)
        graphs = self._expand_graphs([graph] if graph else None)
        graph_filter, graph_params = self._graph_filter(graphs)
        patch_content_predicate = self.expand_iri("rc:patchContent")
        rows = self._conn.execute(
            f"""
            SELECT
                graph,
                subject,
                predicate,
                text,
                snippet(literal_search, 4, '[', ']', ' ... ', 18) AS snippet
            FROM literal_search
            WHERE literal_search MATCH ?
              AND predicate = ?
              {graph_filter}
            ORDER BY bm25(literal_search), graph, subject
            """,
            [fts_query, patch_content_predicate, *graph_params],
        ).fetchall()
        revision_items = self.list_graph_revisions(
            graph=graph,
            include_apply_checks=True,
            current_staged_work_only=False,
            limit=1_000_000,
        )
        revision_by_iri = {item.iri: item for item in revision_items.revisions}
        staged_cache: dict[str, StagedGraphRevisionDescription | None] = {}
        matches: list[StagedPatchPayloadSearchMatch] = []
        for row in rows:
            patch_iri = row["subject"]
            revision_iri = self._first_subject(
                graphs,
                "rc:hasGraphPatch",
                patch_iri,
            )
            if revision_iri is None:
                continue
            revision_item = revision_by_iri.get(revision_iri)
            if (
                current_staged_work_only
                and revision_item is not None
                and not revision_item.is_current_staged_work
            ):
                continue
            staged = self._cached_staged_revision(
                revision_iri,
                graph=graph,
                cache=staged_cache,
            )
            if staged is None:
                continue
            patch = next(
                (candidate for candidate in staged.patches if candidate.iri == patch_iri),
                None,
            )
            if patch is None:
                continue
            matches.append(
                self._staged_patch_payload_search_match(
                    row=row,
                    staged=staged,
                    patch=patch,
                    revision_item=revision_item,
                    search_tokens=search_tokens,
                )
            )

        sliced = matches[offset : offset + limit]
        suggested_next_actions: list[SuggestedNextAction] = []
        seen_action_keys: set[tuple[str, str]] = set()
        for match in sliced:
            for action in match.suggested_next_actions:
                action_key = (
                    action.tool,
                    json.dumps(to_jsonable(action.args), sort_keys=True),
                )
                if action_key in seen_action_keys:
                    continue
                seen_action_keys.add(action_key)
                suggested_next_actions.append(action)
        return StagedPatchPayloadSearchResults(
            query=query,
            graph=graph,
            current_staged_work_only=current_staged_work_only,
            matches=sliced,
            count=len(matches),
            returned_count=len(sliced),
            total_count=len(matches),
            limit=limit,
            offset=offset,
            suggested_next_actions=suggested_next_actions,
        )
    def _staged_patch_payload_search_match(
        self,
        *,
        row: sqlite3.Row,
        staged: StagedGraphRevisionDescription,
        patch: StagedGraphPatchDescription,
        revision_item: GraphRevisionListItem | None,
        search_tokens: list[str],
    ) -> StagedPatchPayloadSearchMatch:
        (
            matched_roles,
            patch_subject_iris,
            parsed_resource_iris,
            parse_error,
        ) = self._staged_patch_payload_parsed_terms(
            patch,
            search_tokens=search_tokens,
        )
        actions = [
            SuggestedNextAction(
                tool="doxabase.describe_revision",
                args={
                    "iri": staged.iri,
                    "include_current_apply_check": True,
                },
                reason="Inspect the staged revision that owns this matching "
                    "patch payload before treating the hit as live graph fact.",
            ),
            SuggestedNextAction(
                tool="doxabase.export_bundle",
                args={
                    "kind": "staged_revisions",
                    "spec": {
                        "revision_iris": [staged.iri],
                        "path": self._staged_patch_payload_search_export_path(
                            staged.iri
                        ),
                        "fail_on_sensitive": True,
                    },
                },
                reason="Export the owning staged revision as a review artifact "
                    "with full Turtle payload and current apply routing. The "
                    "suggested call blocks if scanner-matching content appears "
                    "before export.",
            ),
        ]
        if patch_subject_iris:
            actions.append(
                SuggestedNextAction(
                    tool="doxabase.list_revisions",
                    args={
                        "kind": "resource",
                        "resource_iri": patch_subject_iris[0],
                        "current_staged_work_only": True,
                        "include_patch_mentions": True,
                    },
                    reason="Use resource-centric patch mention discovery for the "
                        "first proposed subject in this staged payload.",
                )
            )
        return StagedPatchPayloadSearchMatch(
            revision_iri=staged.iri,
            revision_summary=staged.summary,
            revision_application_status=(
                revision_item.application_status
                if revision_item is not None
                else None
            ),
            revision_is_current_staged_work=(
                revision_item.is_current_staged_work
                if revision_item is not None
                else None
            ),
            patch_iri=patch.iri,
            graph=row["graph"],
            target_graph=patch.target_graph,
            operation=patch.operation,
            operation_label=patch.operation_label,
            patch_role=patch.patch_role,
            patch_role_label=patch.patch_role_label,
            sequence_index=patch.sequence_index,
            triple_count=patch.triple_count,
            text=row["text"],
            snippet=row["snippet"],
            matched_term_roles=matched_roles,
            patch_subject_iris=patch_subject_iris,
            parsed_resource_iris=parsed_resource_iris,
            parsed_resource_count=len(parsed_resource_iris),
            parse_error=parse_error,
            suggested_next_actions=actions,
        )
    def _staged_patch_payload_parsed_terms(
        self,
        patch: StagedGraphPatchDescription,
        *,
        search_tokens: list[str],
    ) -> tuple[list[str], list[str], list[str], str | None]:
        try:
            graph = self._parse_staged_patch_description(patch)
        except DoxaBaseError as exc:
            return [], [], [], str(exc)

        matched_roles: set[str] = set()
        subject_iris: set[str] = set()
        resource_iris: set[str] = set()

        def matches_token(value: str) -> bool:
            lowered = value.lower()
            return any(token in lowered for token in search_tokens)

        for subject, predicate, object_node in graph:
            if isinstance(subject, URIRef):
                subject_text = str(subject)
                subject_iris.add(subject_text)
                resource_iris.add(subject_text)
                if matches_token(subject_text):
                    matched_roles.add("subject")
            predicate_text = str(predicate)
            resource_iris.add(predicate_text)
            if matches_token(predicate_text):
                matched_roles.add("predicate")
            if isinstance(object_node, URIRef):
                object_text = str(object_node)
                resource_iris.add(object_text)
                if matches_token(object_text):
                    matched_roles.add("object")
            elif isinstance(object_node, Literal) and matches_token(str(object_node)):
                matched_roles.add("literal")

        role_order = ["subject", "predicate", "object", "literal"]
        return (
            [role for role in role_order if role in matched_roles],
            sorted(subject_iris),
            sorted(resource_iris),
            None,
        )
    def _staged_patch_payload_search_export_path(self, revision_iri: str) -> str:
        local = self._local_name(revision_iri) or "revision"
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", local).strip("-") or "revision"
        return f"/tmp/staged-payload-search-{safe}.md"
    def _search_no_match_staged_payload_action(
        self,
        *,
        query: str,
        limit: int,
    ) -> SuggestedNextAction:
        arguments = {
            "query": query,
            "scope": "staged_patches",
            "graph": "history",
            "current_staged_work_only": True,
            "limit": limit,
            "offset": 0,
        }
        return SuggestedNextAction(
                   tool="doxabase.search",
                   args=arguments,
                   reason="The term may exist only inside a current staged proposal. "
                "Search patch payloads before treating proposed ontology, shape, "
                "or map resources as absent.",
               )
    def _current_staged_query_repair_patch_rows(
        self,
        dataset: DatasetDescription,
    ) -> list[dict[str, str]]:
        anchor_iris = self._dataset_query_repair_anchor_iris(dataset.iri, dataset)
        query_repair_predicates = {
            self.expand_iri(predicate) for predicate in QUERY_REPAIR_PREDICATE_CURIES
        }
        history_graphs = self._expand_graphs(["history"])
        addition_operation = self.expand_iri("rc:AdditionPatch")
        removal_operation = self.expand_iri("rc:RemovalPatch")
        rows: list[dict[str, str]] = []
        for revision_iri in self._subjects(
            history_graphs,
            str(RDF.type),
            self.expand_iri("rc:GraphRevision"),
        ):
            if self._first_subject(
                history_graphs,
                "rc:appliesStagedRevision",
                revision_iri,
            ) is not None:
                continue
            if (
                self._current_restage_successor_iri(
                    revision_iri,
                    graphs=history_graphs,
                )
                is not None
            ):
                continue
            revision_anchors = set(
                self._objects(history_graphs, revision_iri, "rc:revisionAnchor")
            )
            if not (anchor_iris & revision_anchors):
                continue
            try:
                staged = self.describe_staged_revision(revision_iri)
            except DoxaBaseError:
                continue
            for patch in staged.patches:
                if patch.target_graph != "map":
                    continue
                if patch.operation == addition_operation:
                    operation = "add"
                elif patch.operation == removal_operation:
                    operation = "remove"
                else:
                    continue
                try:
                    patch_graph = self._parse_staged_patch_description(patch)
                except DoxaBaseError:
                    continue
                for row in self._rdf_graph_storage_rows(patch_graph):
                    if row[2] not in query_repair_predicates:
                        continue
                    rows.append(
                        {
                            "revision_iri": revision_iri,
                            "operation": operation,
                            "subject": row[0],
                            "predicate": row[2],
                            "object": row[3],
                            "object_kind": row[4],
                        }
                    )
        return rows
    def stage_query_physical_layout_repair(
        self,
        dataset_iri: str,
        layout_iri: str,
        *,
        file_format: str,
        rationale: str,
        label: str | None = None,
        description: str | None = None,
        compression_codec: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        allow_existing_physical_layouts: bool = False,
        summary: str | None = None,
        review_note: str | None = None,
        review_recommendation: str | None = None,
        profile_route_sources: Iterable[Mapping[str, Any]] | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
    ) -> StagedGraphRevisionRecord:
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        layout_value = self._required_iri("layout_iri", layout_iri)
        if not allow_existing_physical_layouts:
            dataset = self.describe_dataset(dataset_value)
            if dataset.physical_layouts:
                existing = ", ".join(
                    layout.iri for layout in dataset.physical_layouts[:3]
                )
                raise DoxaBaseError(
                    "stage_revision kind='query_physical_layout_repair' is intended for "
                    "missing_physical_layout repair groups; dataset already "
                    f"has physical layout(s): {existing}. Pass "
                    "allow_existing_physical_layouts=True only after reviewing "
                    "that an additional layout will not create ambiguous query "
                    "targets."
                )
        rationale_value = rationale.strip()
        if not rationale_value:
            raise DoxaBaseError("rationale must not be empty")
        file_format_ref = self._resource_ref("file_format", file_format)
        compression_codec_ref = (
            self._resource_ref("compression_codec", compression_codec)
            if compression_codec is not None
            else None
        )
        layout_verification_status_ref = (
            self._controlled_resource_ref(
                "layout_verification_status",
                layout_verification_status,
                LAYOUT_VERIFICATION_STATUSES,
            )
            if layout_verification_status is not None
            else None
        )
        profile_route_source_values = self._explicit_profile_route_sources(
            profile_route_sources or []
        )
        if profile_route_sources is not None and not profile_route_source_values:
            raise DoxaBaseError(
                "profile_route_sources was provided, but no usable profile "
                "route source entries were found"
            )

        graph_payload = self._query_physical_layout_repair_graph(
            dataset_iri=dataset_value,
            layout_iri=layout_value,
            label=label,
            description=description,
            file_format=file_format_ref,
            compression_codec=compression_codec_ref,
            layout_verification_status=layout_verification_status_ref,
            layout_verification_note=layout_verification_note,
        )
        additions = [
            {
                "graph": "map",
                "format": "turtle",
                "content": graph_payload.serialize(format="turtle"),
            }
        ]
        dataset_label = self._local_name(dataset_value) or dataset_value
        summary_value = (
            summary.strip()
            if summary is not None and summary.strip()
            else f"Stage physical layout repair for {dataset_label}"
        )
        review_note_value = (
            review_note
            if review_note is not None
            else (
                "Generated by stage_query_physical_layout_repair from reviewed "
                "query-planning repair inputs. The helper staged the physical "
                "layout resource and dataset link together instead of writing "
                "current-best map facts directly."
            )
        )
        review_recommendation_value = (
            review_recommendation
            if review_recommendation is not None
            else (
                "Apply only after confirming the layout IRI, file format, and "
                "verification status describe the source data needed for query "
                "planning."
            )
        )
        staged = self.stage_graph_revision(
            summary=summary_value,
            rationale=rationale_value,
            additions=additions,
            revision_anchors=[dataset_value, layout_value],
            included_graphs=["map"],
            review_note=review_note_value,
            review_recommendation=review_recommendation_value,
            validation_scope=validation_scope,
        )
        self._record_profile_insight_route_sources(
            staged.revision_iri,
            profile_route_source_values,
        )
        return staged
    def stage_query_storage_access_repair(
        self,
        dataset_iri: str,
        storage_access_iri: str,
        *,
        storage_protocol: str,
        storage_root: str,
        rationale: str,
        label: str | None = None,
        description: str | None = None,
        route_roles: Iterable[str] | str | None = None,
        access_mode: str | None = None,
        location_kind: str | None = None,
        endpoint_profile: str | None = None,
        bucket_name: str | None = None,
        key_prefix: str | None = None,
        region: str | None = None,
        path_style_access: bool | None = None,
        credential_reference: str | None = None,
        path_templates: Iterable[str] | str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        allow_existing_storage_accesses: bool = False,
        summary: str | None = None,
        review_note: str | None = None,
        review_recommendation: str | None = None,
        profile_route_sources: Iterable[Mapping[str, Any]] | None = None,
        validation_scope: TypingLiteral[
            "map",
            "ontology",
            "patterns",
            "shapes",
            "all",
        ] = "all",
    ) -> StagedGraphRevisionRecord:
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        access_value = self._required_iri("storage_access_iri", storage_access_iri)
        if not allow_existing_storage_accesses:
            dataset = self.describe_dataset(dataset_value)
            if dataset.storage_accesses:
                existing = ", ".join(
                    access.iri for access in dataset.storage_accesses[:3]
                )
                raise DoxaBaseError(
                    "stage_revision kind='query_storage_access_repair' is intended for "
                    "missing_storage_access repair groups; dataset already "
                    f"has storage access resource(s): {existing}. Pass "
                    "allow_existing_storage_accesses=True only after reviewing "
                    "that an additional storage route will not create duplicate "
                    "query target candidates."
                )
        storage_root_value = storage_root.strip()
        if not storage_root_value:
            raise DoxaBaseError("storage_root must not be empty")
        rationale_value = rationale.strip()
        if not rationale_value:
            raise DoxaBaseError("rationale must not be empty")
        route_role_values = self._string_values("route_roles", route_roles)
        path_template_values = self._string_values("path_templates", path_templates)
        location_kind_value = self._storage_location_kind(location_kind)
        storage_protocol_ref = self._resource_ref(
            "storage_protocol",
            storage_protocol,
        )
        access_mode_ref = (
            self._resource_ref("access_mode", access_mode)
            if access_mode is not None
            else None
        )
        layout_verification_status_ref = (
            self._controlled_resource_ref(
                "layout_verification_status",
                layout_verification_status,
                LAYOUT_VERIFICATION_STATUSES,
            )
            if layout_verification_status is not None
            else None
        )
        profile_route_source_values = self._explicit_profile_route_sources(
            profile_route_sources or []
        )
        if profile_route_sources is not None and not profile_route_source_values:
            raise DoxaBaseError(
                "profile_route_sources was provided, but no usable profile "
                "route source entries were found"
            )

        graph_payload = self._query_storage_access_repair_graph(
            dataset_iri=dataset_value,
            storage_access_iri=access_value,
            label=label,
            description=description,
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
            layout_verification_status=layout_verification_status_ref,
            layout_verification_note=layout_verification_note,
        )
        additions = [
            {
                "graph": "map",
                "format": "turtle",
                "content": graph_payload.serialize(format="turtle"),
            }
        ]
        dataset_label = self._local_name(dataset_value) or dataset_value
        summary_value = (
            summary.strip()
            if summary is not None and summary.strip()
            else f"Stage storage access repair for {dataset_label}"
        )
        review_note_value = (
            review_note
            if review_note is not None
            else (
                "Generated by stage_query_storage_access_repair from reviewed "
                "query-planning repair inputs. The helper staged the storage "
                "access resource and dataset link together instead of writing "
                "current-best map facts directly."
            )
        )
        review_recommendation_value = (
            review_recommendation
            if review_recommendation is not None
            else (
                "Apply only after confirming the storage protocol, non-secret "
                "location, and path or relation templates describe the intended "
                "source data for query planning."
            )
        )
        staged = self.stage_graph_revision(
            summary=summary_value,
            rationale=rationale_value,
            additions=additions,
            revision_anchors=[dataset_value, access_value],
            included_graphs=["map"],
            review_note=review_note_value,
            review_recommendation=review_recommendation_value,
            validation_scope=validation_scope,
        )
        self._record_profile_insight_route_sources(
            staged.revision_iri,
            profile_route_source_values,
        )
        return staged
    def _pending_staged_storage_access_links(
        self,
        dataset_iri: str,
    ) -> dict[str, list[str]]:
        history_graphs = self._expand_graphs(["history"])
        dataset_ref = URIRef(self.expand_iri(dataset_iri))
        predicate_ref = URIRef(self.expand_iri("rc:hasStorageAccess"))
        addition_operation = self.expand_iri("rc:AdditionPatch")
        pending_by_storage: dict[str, list[str]] = {}
        for revision_iri in self._subjects(
            history_graphs,
            str(RDF.type),
            self.expand_iri("rc:GraphRevision"),
        ):
            patch_iris = self._objects(
                history_graphs,
                revision_iri,
                "rc:hasGraphPatch",
            )
            if not patch_iris:
                continue
            item_revision_type = self._first_object(
                history_graphs,
                revision_iri,
                "rc:revisionType",
            )
            applies_staged_revision = self._first_object(
                history_graphs,
                revision_iri,
                "rc:appliesStagedRevision",
            )
            if (
                self._graph_revision_record_kind(
                    item_revision_type,
                    has_patch_payload=True,
                    applies_staged_revision=applies_staged_revision,
                )
                != "staged_patch"
            ):
                continue
            if self._first_subject(
                history_graphs,
                "rc:appliesStagedRevision",
                revision_iri,
            ) is not None:
                continue
            if (
                self._current_restage_successor_iri(
                    revision_iri,
                    graphs=history_graphs,
                )
                is not None
            ):
                continue
            try:
                staged = self.describe_staged_revision(revision_iri)
            except DoxaBaseError:
                continue
            for patch in staged.patches:
                if patch.operation != addition_operation:
                    continue
                if patch.target_graph != "map":
                    continue
                try:
                    patch_graph = self._parse_staged_patch_description(patch)
                except DoxaBaseError:
                    continue
                for subject, predicate, object_node in patch_graph:
                    if subject != dataset_ref or predicate != predicate_ref:
                        continue
                    if not isinstance(object_node, URIRef):
                        continue
                    pending_by_storage.setdefault(str(object_node), []).append(
                        revision_iri
                    )
        return {
            storage_iri: list(dict.fromkeys(revision_iris))
            for storage_iri, revision_iris in pending_by_storage.items()
        }
    def _pending_staged_metric_promotion_iris(
        self,
        *,
        metric_iri: str,
        evidence_iri: str,
        promotion_pattern_iris: Iterable[str],
    ) -> list[str]:
        data_graphs = self._expand_graphs(["history"])
        metric_value = self.expand_iri(metric_iri)
        evidence_value = self.expand_iri(evidence_iri)
        promotion_pattern_values = {
            self.expand_iri(pattern_iri) for pattern_iri in promotion_pattern_iris
        }
        if not promotion_pattern_values:
            return []

        candidates: list[tuple[str, str]] = []
        for revision_iri in self._subjects(
            data_graphs,
            "rc:revisionAnchor",
            metric_value,
        ):
            if self._first_subject(
                data_graphs,
                "rc:appliesStagedRevision",
                revision_iri,
            ):
                continue
            if self._current_restage_successor_iri(revision_iri, graphs=data_graphs):
                continue
            if not self._objects(data_graphs, revision_iri, "rc:hasGraphPatch"):
                continue
            review_note = self._first_object(
                data_graphs,
                revision_iri,
                "rc:reviewNote",
            )
            if (
                PROFILE_METRIC_PROMOTION_REVIEW_NOTE_MARKER
                not in (review_note or "")
            ):
                continue
            if evidence_value not in self._objects(
                data_graphs,
                revision_iri,
                "rc:evidence",
            ):
                continue
            supporting_patterns = set(
                self._objects(
                    data_graphs,
                    revision_iri,
                    "rc:revisionSupportingPattern",
                )
            )
            if not promotion_pattern_values & supporting_patterns:
                continue
            created_at = (
                self._first_object(data_graphs, revision_iri, "rc:createdAt") or ""
            )
            candidates.append((created_at, revision_iri))
        return [
            revision_iri
            for _, revision_iri in sorted(
                candidates,
                key=lambda item: (item[0], item[1]),
                reverse=True,
            )
        ]
