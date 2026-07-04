"""Entity listing and resource/assertion description.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via EntitiesMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class EntitiesMixin:
    def list_entities(
        self,
        type: str | None = None,
        graph: str | None = "map",
        text: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> EntityList:
        if limit < 1:
            raise DoxaBaseError("Entity list limit must be at least 1")
        if offset < 0:
            raise DoxaBaseError("Entity list offset must be non-negative")

        graphs = self._expand_graphs([graph] if graph else None)
        params: list[Any] = []
        graph_filter = ""
        if graphs:
            graph_filter = f"AND q.graph IN ({','.join('?' for _ in graphs)})"
            params.extend(graphs)

        type_filter = ""
        if type:
            type_filter = """
                AND EXISTS (
                    SELECT 1
                    FROM quads qt
                    WHERE qt.graph = q.graph
                      AND qt.subject = q.subject
                      AND qt.predicate = ?
                      AND qt.object = ?
                )
            """
            params.extend([str(RDF.type), self.expand_iri(type)])

        text_filter = ""
        if text:
            text_filter = """
                AND (
                    lower(q.subject) LIKE ?
                    OR EXISTS (
                        SELECT 1
                        FROM quads ql
                        WHERE ql.graph = q.graph
                          AND ql.subject = q.subject
                          AND ql.object_kind IN ('literal', 'uri')
                          AND lower(ql.object) LIKE ?
                    )
                )
            """
            needle = f"%{text.lower()}%"
            params.extend([needle, needle])

        total_count = int(
            self._conn.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM (
                    SELECT q.graph, q.subject
                    FROM quads q
                    WHERE q.subject_kind IN ('uri', 'bnode')
                      {graph_filter}
                      {type_filter}
                      {text_filter}
                    GROUP BY q.graph, q.subject
                ) AS grouped_entities
                """,
                params,
            ).fetchone()["count"]
        )

        rows = self._conn.execute(
            f"""
            SELECT q.graph, q.subject
            FROM quads q
            WHERE q.subject_kind IN ('uri', 'bnode')
              {graph_filter}
              {type_filter}
              {text_filter}
            GROUP BY q.graph, q.subject
            ORDER BY q.subject
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()

        entities = [
            EntityRow(
                iri=row["subject"],
                label=self._display_label_from_graphs(
                    self._lookup_graphs([row["graph"]]),
                    row["subject"],
                ),
                types=self._types(row["graph"], row["subject"]),
                graph=row["graph"],
            )
            for row in rows
        ]
        returned_count = len(entities)
        next_offset = (
            offset + returned_count
            if offset + returned_count < total_count
            else None
        )
        suggested_next_actions = (
            [
                self._list_entities_next_page_action(
                    type=type,
                    graph=graph,
                    text=text,
                    limit=limit,
                    offset=next_offset,
                )
            ]
            if next_offset is not None
            else []
        )
        return EntityList(
            entities=entities,
            limit=limit,
            offset=offset,
            returned_count=returned_count,
            total_count=total_count,
            omitted_count=max(total_count - offset - returned_count, 0),
            has_more=next_offset is not None,
            next_offset=next_offset,
            suggested_next_actions=suggested_next_actions,
        )
    def _list_entities_next_page_action(
        self,
        *,
        type: str | None,
        graph: str | None,
        text: str | None,
        limit: int,
        offset: int,
    ) -> SuggestedNextAction:
        arguments: dict[str, Any] = {"limit": limit, "offset": offset}
        if type is not None:
            arguments["type"] = type
        if graph is not None:
            arguments["graph"] = graph
        if text is not None:
            arguments["text"] = text
        return SuggestedNextAction(
                   tool="doxabase.list_entities",
                   args=arguments,
                   reason="More matching entities exist beyond the returned page.",
               )
    def describe_resource(
        self,
        iri: str,
        *,
        graph: str | None = None,
        include_incoming: bool = True,
        limit: int = 100,
        outgoing_offset: int = 0,
        incoming_offset: int = 0,
        include_blank_node_closure: bool = False,
        blank_node_depth: int = 2,
        blank_node_limit: int = 100,
    ) -> ResourceContext:
        if limit < 1:
            raise DoxaBaseError("Resource context limit must be at least 1")
        if outgoing_offset < 0:
            raise DoxaBaseError("outgoing_offset must be non-negative")
        if incoming_offset < 0:
            raise DoxaBaseError("incoming_offset must be non-negative")
        if blank_node_depth < 0:
            raise DoxaBaseError("blank_node_depth must be non-negative")
        if blank_node_limit < 1:
            raise DoxaBaseError("blank_node_limit must be at least 1")
        resource_iri = self.expand_iri(iri)
        graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(graphs)
        types = self._types_from_graphs(graphs, resource_iri)
        claim = (
            self._describe_claim(resource_iri, graphs, lookup_graphs)
            if self.expand_iri("rc:Claim") in types
            else None
        )
        outgoing_total_count = self._resource_triple_count(
            graphs,
            subject=resource_iri,
        )
        incoming_total_count = (
            self._resource_triple_count(
                graphs,
                object_value=resource_iri,
                object_kind="uri",
            )
            if include_incoming
            else 0
        )
        outgoing = self._resource_triples(
            graphs,
            subject=resource_iri,
            limit=limit,
            offset=outgoing_offset,
        )
        incoming = (
            self._resource_triples(
                graphs,
                object_value=resource_iri,
                object_kind="uri",
                limit=limit,
                offset=incoming_offset,
            )
            if include_incoming
            else []
        )
        blank_node_triples: list[ResourceTriple] = []
        blank_node_total_count = 0
        blank_node_depth_exhausted = False
        blank_node_unvisited_count = 0
        if include_blank_node_closure:
            (
                blank_node_triples,
                blank_node_total_count,
                blank_node_depth_exhausted,
                blank_node_unvisited_count,
            ) = self._resource_blank_node_closure(
                graphs,
                subject=resource_iri,
                max_depth=blank_node_depth,
                limit=blank_node_limit,
            )
        return ResourceContext(
            iri=resource_iri,
            graph=graph,
            label=self._display_label_from_graphs(lookup_graphs, resource_iri),
            description=self._description_from_graphs(lookup_graphs, resource_iri),
            types=types,
            claim=claim,
            outgoing=outgoing,
            incoming=incoming,
            blank_node_triples=blank_node_triples,
            limit=limit,
            outgoing_offset=outgoing_offset,
            incoming_offset=incoming_offset,
            outgoing_total_count=outgoing_total_count,
            outgoing_returned_count=len(outgoing),
            outgoing_omitted_count=max(
                outgoing_total_count - outgoing_offset - len(outgoing),
                0,
            ),
            incoming_total_count=incoming_total_count,
            incoming_returned_count=len(incoming),
            incoming_omitted_count=max(
                incoming_total_count - incoming_offset - len(incoming),
                0,
            ),
            include_blank_node_closure=include_blank_node_closure,
            blank_node_depth=blank_node_depth,
            blank_node_limit=blank_node_limit,
            blank_node_total_count=blank_node_total_count,
            blank_node_returned_count=len(blank_node_triples),
            blank_node_omitted_count=max(
                blank_node_total_count - len(blank_node_triples),
                0,
            ),
            blank_node_depth_exhausted=blank_node_depth_exhausted,
            blank_node_unvisited_count=blank_node_unvisited_count,
        )
    def describe_assertion_support(
        self,
        subject: str,
        predicate: str,
        object: str | None = None,
        *,
        graph: str | None = "map",
        object_kind: TypingLiteral["auto", "iri", "uri", "literal"] = "auto",
        object_datatype: str | None = None,
        object_lang: str | None = None,
        limit: int = 20,
    ) -> AssertionSupportDescription:
        if limit < 1:
            raise DoxaBaseError("Assertion support limit must be at least 1")
        subject_iri = self.expand_iri(subject)
        predicate_iri = self.expand_iri(predicate)
        graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))
        object_filter = self._assertion_object_filter(
            object,
            object_kind,
            object_datatype=object_datatype,
            object_lang=object_lang,
        )
        matching_triples = self._assertion_triples(
            graphs,
            subject=subject_iri,
            predicate=predicate_iri,
            object_filter=object_filter,
            limit=limit,
        )
        if object_filter is not None and not matching_triples:
            matching_triples = self._assertion_compatible_literal_triples(
                graphs,
                subject=subject_iri,
                predicate=predicate_iri,
                object_filter=object_filter,
                limit=limit,
            )
        same_subject_predicate_triples = (
            self._assertion_triples(
                graphs,
                subject=subject_iri,
                predicate=predicate_iri,
                object_filter=None,
                limit=limit,
            )
            if object_filter is not None
            else matching_triples
        )
        requested_object = (
            self._assertion_value_from_filter(lookup_graphs, object_filter)
            if object_filter is not None
            else None
        )
        target_iris = self._assertion_target_iris(
            subject_iri,
            same_subject_predicate_triples,
            requested_object,
        )
        related = self._staged_revision_related_lore(target_iris)
        related_routes = self._assertion_related_lore_routes(target_iris)
        related_route_summaries = self._assertion_related_route_summaries(
            related_routes,
            subject_iri=subject_iri,
        )
        nearby_caveat_links = self._assertion_nearby_caveat_links(
            target_iris,
            lookup_graphs,
        )
        nearby_caveats = self._caveats_from_links(nearby_caveat_links)
        target_resources = self._resource_summaries(lookup_graphs, target_iris)
        subject_summary = self._resource_summary(lookup_graphs, subject_iri)
        owner_dataset = (
            self._resource_summary(lookup_graphs, subject_summary.owning_dataset_iri)
            if subject_summary.owning_dataset_iri is not None
            else None
        )
        dataset_context_iris = self._assertion_dataset_context_iris(
            lookup_graphs,
            target_resources,
        )
        nearby_context_iris = [*target_iris, *dataset_context_iris]
        nearby_context_triples = self._assertion_nearby_context_triples(
            nearby_context_iris,
            lookup_graphs,
            limit=limit,
        )
        predicate_hints = (
            self._assertion_predicate_hints(
                subject_iri,
                predicate_iri,
                graphs,
                lookup_graphs,
                limit=min(limit, 8),
            )
            if not same_subject_predicate_triples
            else []
        )
        context_note = (
            "Assertion support is a retrieval aid, not proof. It gathers nearby "
            "observations, claims, patterns, evidence, revisions, and caveats linked "
            "to the assertion's subject, requested object, and current object "
            "resources for the same subject/predicate. It also surfaces selected "
            "direct layout/path context facts on those resources."
        )
        support_scope_note = (
            "Exact assertion and same-subject predicate triples are read from the "
            f"{graph or 'selected'} graph selection. Lore is gathered for the subject, "
            "the requested object when supplied, and any current object resources "
            "for the same subject/predicate. Column targets also pull caveats from "
            "their owning dataset, but owner-dataset observations, claims, patterns, "
            "evidence, and revisions only appear when directly linked through the "
            "gathered target resources. Nearby context triples are limited to direct "
            "layout/path predicates that often affect whether a map assertion is safe "
            "to use for executable planning."
        )
        if owner_dataset is not None:
            support_scope_note += (
                " The subject is a column with an owning dataset; inspect "
                "owner_dataset and the owner-seeded suggested actions for broader "
                "dataset lore."
            )
        elif dataset_context_iris:
            support_scope_note += (
                " Dataset-context suggested actions are seeded from dataset/table "
                "targets and owning datasets discovered around the assertion."
            )
        absence_note = self._assertion_absence_note(
            matching_triples,
            same_subject_predicate_triples,
            requested_object,
            predicate_hints,
        )
        has_related_lore = any(related.values())
        if not has_related_lore and (nearby_caveats or nearby_context_triples):
            context_note += (
                " No related observations, claims, patterns, evidence, or revisions "
                "were found in this scoped lookup; inspect nearby caveats/context "
                "and follow the suggested actions before treating that as a broad "
                "absence of project lore."
            )
        elif not has_related_lore:
            context_note += (
                " No linked lore, nearby caveats, or nearby layout/path context facts "
                "were found in this scoped lookup; follow the suggested actions before "
                "treating that as a broad absence of project lore."
            )
        suggested_next_actions = self._assertion_support_next_actions(
            subject_iri,
            predicate_iri,
            requested_object,
            graph=graph,
            dataset_context_iris=dataset_context_iris,
        )

        return AssertionSupportDescription(
            graph=graph,
            subject=subject_summary,
            owner_dataset=owner_dataset,
            predicate=predicate_iri,
            predicate_label=self._label_for_resource(predicate_iri),
            requested_object=requested_object,
            assertion_present=bool(matching_triples),
            matching_triples=matching_triples,
            same_subject_predicate_triples=same_subject_predicate_triples,
            target_resources=target_resources,
            nearby_caveats=nearby_caveats,
            nearby_caveat_links=nearby_caveat_links,
            nearby_context_triples=nearby_context_triples,
            related_observations=related["observations"],
            related_claims=related["claims"],
            related_patterns=related["patterns"],
            related_evidence=related["evidence"],
            related_revisions=related["revisions"],
            related_routes=related_routes,
            related_route_summaries=related_route_summaries,
            predicate_hints=predicate_hints,
            context_note=context_note,
            support_scope_note=support_scope_note,
            absence_note=absence_note,
            suggested_next_actions=suggested_next_actions,
        )
    def _draft_assertion_support_review_arguments(
        self,
        prepared: _MapAssertionChangePrepared,
        *,
        limit: int,
    ) -> dict[str, Any]:
        arguments: dict[str, Any] = {
            "iri": prepared.subject,
            "aspect": "assertion_support",
            "predicate": prepared.predicate,
            "graph": prepared.graph,
        }
        if prepared.object_value is not None:
            arguments["object"] = prepared.object_value
            arguments["object_kind"] = prepared.stage_arguments.get(
                "object_kind",
                "auto",
            )
            if prepared.object_datatype is not None:
                arguments["object_datatype"] = prepared.object_datatype
            if prepared.object_lang is not None:
                arguments["object_lang"] = prepared.object_lang
        if limit != 20:
            arguments["limit"] = limit
        return arguments
    @staticmethod
    def _graph_storage_row_mentions_resource(
        row: GraphStorageRow,
        resource_iri: str,
    ) -> bool:
        return (
            row[0] == resource_iri
            or row[2] == resource_iri
            or (row[4] == "uri" and row[3] == resource_iri)
        )
    def _resource_triple_object_term(self, triple: ResourceTriple) -> Identifier:
        if triple.object_kind == "uri":
            return URIRef(triple.object)
        if triple.object_kind == "bnode":
            return BNode(triple.object)
        if triple.object_kind == "literal":
            return Literal(
                triple.object,
                lang=triple.object_lang,
                datatype=triple.object_datatype,
            )
        raise TypeError(f"Unsupported object kind: {triple.object_kind}")
    @staticmethod
    def _add_mixed_support_review_note(
        arguments: dict[str, Any],
        mixed_support_note: str,
    ) -> None:
        if "framings" in arguments:
            for framing in arguments.get("framings") or []:
                framing["review_note"] = (
                    f"{framing.get('review_note') or ''} {mixed_support_note}"
                ).strip()
                framing["review_recommendation"] = (
                    f"{framing.get('review_recommendation') or ''} "
                    f"{mixed_support_note}"
                ).strip()
            return
        arguments["review_note"] = (
            f"{arguments.get('review_note') or ''} {mixed_support_note}"
        ).strip()
        arguments["review_recommendation"] = (
            f"{arguments.get('review_recommendation') or ''} "
            f"{mixed_support_note}"
        ).strip()
    def _changed_graph_resource_summary(
        self,
        *,
        triples_added: Iterable[GraphTripleDescription],
        triples_removed: Iterable[GraphTripleDescription],
        patch_terms: _StagedRevisionDriftTerms | None = None,
        source_revision_iri: str | None = None,
        max_resources: int = 12,
        max_predicates_per_resource: int = 8,
    ) -> tuple[
        int,
        int,
        int,
        list[ChangedGraphResourceSummary],
        list[SuggestedNextAction],
    ]:
        accumulators: dict[str, _ChangedGraphResourceAccumulator] = {}

        def accumulator(iri: str) -> _ChangedGraphResourceAccumulator:
            if iri not in accumulators:
                accumulators[iri] = _ChangedGraphResourceAccumulator(iri=iri)
            return accumulators[iri]

        def collect(
            triple: GraphTripleDescription,
            *,
            change_kind: TypingLiteral["added", "removed"],
        ) -> None:
            resources: dict[str, set[str]] = {}
            if triple.subject_kind == "uri":
                resources.setdefault(triple.subject, set()).add("changed_subject")
            if triple.object_kind == "uri":
                resources.setdefault(triple.object, set()).add("changed_object")
            for iri, roles in resources.items():
                acc = accumulator(iri)
                if change_kind == "added":
                    acc.added_triple_count += 1
                else:
                    acc.removed_triple_count += 1
                acc.matched_by.update(roles)
                acc.predicate_iris.add(triple.predicate)

        for triple in triples_added:
            collect(triple, change_kind="added")
        for triple in triples_removed:
            collect(triple, change_kind="removed")

        if patch_terms is not None:
            for iri, acc in accumulators.items():
                if iri in patch_terms.patch_subjects:
                    acc.matched_by.add("patch_subject")
                if iri in patch_terms.patch_objects:
                    acc.matched_by.add("patch_object")
                if iri in patch_terms.revision_anchors:
                    acc.matched_by.add("revision_anchor")

        role_order = {
            "patch_subject": 0,
            "revision_anchor": 1,
            "patch_object": 2,
            "changed_subject": 3,
            "changed_object": 4,
        }

        def sort_key(acc: _ChangedGraphResourceAccumulator) -> tuple[int, int, str]:
            rank = min((role_order.get(role, 99) for role in acc.matched_by), default=99)
            changed_count = acc.added_triple_count + acc.removed_triple_count
            return (rank, -changed_count, acc.iri)

        ordered = sorted(accumulators.values(), key=sort_key)
        returned = ordered[:max_resources]
        lookup_graphs = self._lookup_graphs(self._expand_graphs(["all"]))
        summaries: list[ChangedGraphResourceSummary] = []
        for acc in returned:
            predicate_iris = sorted(acc.predicate_iris)[:max_predicates_per_resource]
            summaries.append(
                ChangedGraphResourceSummary(
                    resource=self._resource_summary(lookup_graphs, acc.iri),
                    changed_triple_count=(
                        acc.added_triple_count + acc.removed_triple_count
                    ),
                    added_triple_count=acc.added_triple_count,
                    removed_triple_count=acc.removed_triple_count,
                    matched_by=sorted(
                        acc.matched_by,
                        key=lambda role: (role_order.get(role, 99), role),
                    ),
                    predicate_iris=predicate_iris,
                    predicate_displays=[
                        self._graph_term_display(
                            predicate,
                            "uri",
                            curie=self._compact_iri(predicate),
                        )
                        for predicate in predicate_iris
                    ],
                )
            )
        actions = [
            self._changed_graph_resource_suggested_action(
                summary,
                source_revision_iri=source_revision_iri,
            )
            for summary in summaries
        ]
        total = len(ordered)
        return total, len(summaries), max(total - len(summaries), 0), summaries, actions
    def _changed_graph_resource_suggested_action(
        self,
        summary: ChangedGraphResourceSummary,
        *,
        source_revision_iri: str | None,
    ) -> SuggestedNextAction:
        resource_iri = summary.resource.iri
        if source_revision_iri is not None and any(
            role in summary.matched_by
            for role in ("patch_subject", "patch_object", "revision_anchor")
        ):
            arguments: dict[str, Any] = {
                "resource_iri": resource_iri,
                "revision_iri": source_revision_iri,
            }
            tool_name = "describe_resource_revision_lineage"
            return SuggestedNextAction(
                       tool=f"doxabase.{tool_name}",
                       args=arguments,
                       reason="This changed resource overlaps a staged patch subject, "
                    "patch object, or revision anchor; inspect its resource-level "
                    "revision route before restaging or applying.",
                   )
        arguments = {
            "resource_iri": resource_iri,
            "include_patch_mentions": True,
            "include_apply_checks": True,
        }
        tool_name = "list_resource_revisions"
        return SuggestedNextAction(
                   tool=f"doxabase.{tool_name}",
                   args=arguments,
                   reason="Review other staged, applied, or historical revision records "
                "that mention this changed resource before deciding whether "
                "the graph drift is relevant.",
               )
    def _impact_resource_summary(
        self,
        lookup_graphs: list[str],
        node: Node,
    ) -> ResourceSummary | None:
        if isinstance(node, Literal):
            return None
        return self._resource_summary(lookup_graphs, str(node))
    def _assertion_object_filter(
        self,
        object_value: str | None,
        object_kind: str,
        *,
        object_datatype: str | None = None,
        object_lang: str | None = None,
    ) -> tuple[str, str, str | None, str | None] | None:
        if object_value is None:
            if object_datatype is not None or object_lang is not None:
                raise DoxaBaseError(
                    "object_datatype and object_lang require an object value"
                )
            return None
        kind = object_kind.strip().lower()
        if kind == "uri":
            kind = "iri"
        datatype = object_datatype.strip() if object_datatype is not None else None
        if datatype == "":
            datatype = None
        lang = object_lang.strip() if object_lang is not None else None
        if lang == "":
            lang = None
        if datatype is not None and lang is not None:
            raise DoxaBaseError(
                "Literal assertions cannot specify both object_datatype and object_lang"
            )
        if datatype is not None or lang is not None:
            if kind == "iri":
                raise DoxaBaseError(
                    "object_datatype and object_lang can only be used with literal objects"
                )
            node = Literal(
                object_value,
                datatype=URIRef(self.expand_iri(datatype)) if datatype else None,
                lang=lang,
            )
            return self._object_to_storage(node)
        if kind == "auto":
            node = self._resource_or_literal(object_value)
        elif kind == "iri":
            node = URIRef(self.expand_iri(object_value))
        elif kind == "literal":
            node = Literal(object_value)
        else:
            raise DoxaBaseError(
                "object_kind must be one of 'auto', 'iri', 'uri', or 'literal'"
            )
        return self._object_to_storage(node)
    def _assertion_compatible_literal_filters(
        self,
        object_filter: tuple[str, str, str | None, str | None],
    ) -> list[tuple[str, str, str | None, str | None]]:
        value, value_kind, datatype, lang = object_filter
        if value_kind != "literal" or datatype is not None or lang is not None:
            return []

        candidates: list[tuple[str, str, str | None, str | None]] = [
            (value, "literal", str(XSD.string), None),
        ]
        normalized = value.strip()
        lowered = normalized.lower()
        if lowered in {"true", "false"}:
            candidates.append((lowered, "literal", str(XSD.boolean), None))
        if re.fullmatch(r"[+-]?\d+", normalized):
            candidates.append((str(int(normalized)), "literal", str(XSD.integer), None))

        compatible: list[tuple[str, str, str | None, str | None]] = []
        seen = {object_filter}
        for candidate in candidates:
            if candidate not in seen:
                compatible.append(candidate)
                seen.add(candidate)
        return compatible
    def _assertion_compatible_literal_triples(
        self,
        graphs: list[str],
        *,
        subject: str,
        predicate: str,
        object_filter: tuple[str, str, str | None, str | None],
        limit: int,
    ) -> list[ResourceTriple]:
        triples: list[ResourceTriple] = []
        seen: set[tuple[str, str, str, str, str | None, str | None]] = set()
        for compatible_filter in self._assertion_compatible_literal_filters(
            object_filter
        ):
            remaining = limit - len(triples)
            if remaining < 1:
                break
            for triple in self._assertion_triples(
                graphs,
                subject=subject,
                predicate=predicate,
                object_filter=compatible_filter,
                limit=remaining,
            ):
                key = (
                    triple.graph,
                    triple.subject,
                    triple.predicate,
                    triple.object,
                    triple.object_datatype,
                    triple.object_lang,
                )
                if key not in seen:
                    triples.append(triple)
                    seen.add(key)
        return triples
    def _assertion_value_from_filter(
        self,
        lookup_graphs: list[str],
        object_filter: tuple[str, str, str | None, str | None],
    ) -> AssertionValue:
        value, value_kind, datatype, lang = object_filter
        if value_kind in {"uri", "bnode"}:
            resource = self._resource_summary(lookup_graphs, value)
            return AssertionValue(
                value=value,
                value_label=resource.label,
                value_kind="iri" if value_kind == "uri" else "blank_node",
                datatype=datatype,
                lang=lang,
                resource=resource,
                caveat=self._impact_caveat_description(lookup_graphs, value),
            )
        return AssertionValue(
            value=value,
            value_label=None,
            value_kind="literal",
            datatype=datatype,
            lang=lang,
        )
    def _object_node_from_resource_triple(self, triple: ResourceTriple) -> Node:
        if triple.object_kind == "uri":
            return URIRef(triple.object)
        if triple.object_kind == "bnode":
            return BNode(triple.object)
        if triple.object_kind == "literal":
            return Literal(
                triple.object,
                datatype=(
                    URIRef(triple.object_datatype)
                    if triple.object_datatype is not None
                    else None
                ),
                lang=triple.object_lang,
            )
        raise DoxaBaseError(
            f"Unsupported resource triple object kind '{triple.object_kind}'"
        )
    def _subject_node_from_resource_triple(self, triple: ResourceTriple) -> Identifier:
        if triple.subject_kind == "uri":
            return URIRef(triple.subject)
        if triple.subject_kind == "bnode":
            return BNode(triple.subject)
        raise DoxaBaseError(
            f"Unsupported resource triple subject kind '{triple.subject_kind}'"
        )
    def _resource_triple_matches_filter(
        self,
        triple: ResourceTriple,
        object_filter: tuple[str, str, str | None, str | None],
    ) -> bool:
        value, value_kind, datatype, lang = object_filter
        return (
            triple.object == value
            and triple.object_kind == value_kind
            and triple.object_datatype == datatype
            and triple.object_lang == lang
        )
    def _patch_content_from_resource_triples(
        self,
        triples: Iterable[ResourceTriple],
    ) -> str:
        return self._patch_content_from_triples(
            (
                self._subject_node_from_resource_triple(triple),
                URIRef(triple.predicate),
                self._object_node_from_resource_triple(triple),
            )
            for triple in triples
        )
    def _is_generic_shared_value_resource(self, iri: str) -> bool:
        if not iri.startswith(PREFIXES["rc"]):
            return False
        generic_types = {
            self.expand_iri("rc:PhysicalType"),
            self.expand_iri("rc:ValueType"),
            self.expand_iri("rc:RowSemanticsType"),
            self.expand_iri("rc:ConfidenceLevel"),
            self.expand_iri("rc:ObservationStatus"),
            self.expand_iri("rc:PatternStability"),
            self.expand_iri("rc:RevisionStance"),
        }
        resource_types = set(
            self._types_from_graphs(self._expand_graphs(["all"]), iri)
        )
        return bool(resource_types & generic_types)
    def _assertion_target_iris(
        self,
        subject_iri: str,
        matching_triples: Iterable[ResourceTriple],
        requested_object: AssertionValue | None,
    ) -> list[str]:
        target_iris = [subject_iri]
        if requested_object is not None and requested_object.value_kind in {
            "iri",
            "blank_node",
        }:
            target_iris.append(requested_object.value)
        for triple in matching_triples:
            if triple.object_kind in {"uri", "bnode"}:
                target_iris.append(triple.object)
        return list(dict.fromkeys(target_iris))
    def _assertion_nearby_context_triples(
        self,
        target_iris: Iterable[str],
        lookup_graphs: list[str],
        *,
        limit: int,
    ) -> list[ResourceTriple]:
        targets = [
            iri
            for iri in dict.fromkeys(target_iris)
            if iri and not iri.startswith("_:")
        ]
        if not targets:
            return []
        predicates = [
            self.expand_iri("rc:layoutVerificationStatus"),
            self.expand_iri("rc:layoutVerificationNote"),
            self.expand_iri("rc:pathTemplate"),
        ]
        graph_filter, graph_params = self._graph_filter(lookup_graphs, alias="q")
        target_placeholders = ",".join("?" for _ in targets)
        predicate_placeholders = ",".join("?" for _ in predicates)
        rows = self._conn.execute(
            f"""
            SELECT
                q.graph,
                q.subject,
                q.subject_kind,
                q.predicate,
                q.object,
                q.object_kind,
                q.datatype,
                q.lang
            FROM quads q
            WHERE q.subject IN ({target_placeholders})
              AND q.predicate IN ({predicate_placeholders})
              {graph_filter}
            ORDER BY q.graph, q.subject, q.predicate, q.object
            LIMIT ?
            """,
            [*targets, *predicates, *graph_params, limit],
        ).fetchall()
        return [self._resource_triple_from_row(row) for row in rows]
    def _assertion_predicate_hints(
        self,
        subject_iri: str,
        predicate_iri: str,
        graphs: list[str],
        lookup_graphs: list[str],
        *,
        limit: int,
    ) -> list[AssertionPredicateHint]:
        if limit < 1:
            return []
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        rows = self._conn.execute(
            f"""
            SELECT q.predicate, COUNT(*) AS triple_count
            FROM quads q
            WHERE q.subject = ?
              AND q.predicate != ?
              {graph_filter}
            GROUP BY q.predicate
            """,
            [subject_iri, predicate_iri, *graph_params],
        ).fetchall()
        skipped = {str(RDF.type), str(RDFS.label), str(RDFS.comment)}
        scored: list[tuple[float, str, int]] = []
        for row in rows:
            predicate = row["predicate"]
            if predicate in skipped:
                continue
            score = self._predicate_hint_score(predicate_iri, predicate)
            scored.append((score, predicate, int(row["triple_count"])))
        scored.sort(
            key=lambda item: (
                -item[0],
                self._label_for_resource(item[1])
                or self._local_name(item[1])
                or item[1],
            )
        )
        return [
            AssertionPredicateHint(
                predicate=predicate,
                predicate_curie=self._compact_iri(predicate),
                predicate_label=self._label_for_resource(predicate),
                predicate_description=self._description_from_graphs(
                    lookup_graphs,
                    predicate,
                ),
                triple_count=triple_count,
                sample_values=self._assertion_predicate_hint_sample_values(
                    subject_iri,
                    predicate,
                    graphs,
                    lookup_graphs,
                ),
            )
            for _, predicate, triple_count in scored[:limit]
        ]
    def _assertion_predicate_hint_sample_values(
        self,
        subject_iri: str,
        predicate_iri: str,
        graphs: list[str],
        lookup_graphs: list[str],
        *,
        limit: int = 3,
    ) -> list[AssertionValue]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        rows = self._conn.execute(
            f"""
            SELECT q.object, q.object_kind, q.datatype, q.lang
            FROM quads q
            WHERE q.subject = ?
              AND q.predicate = ?
              {graph_filter}
            ORDER BY q.object
            LIMIT ?
            """,
            [subject_iri, predicate_iri, *graph_params, limit],
        ).fetchall()
        return [
            self._assertion_value_from_filter(
                lookup_graphs,
                (
                    row["object"],
                    row["object_kind"],
                    row["datatype"],
                    row["lang"],
                ),
            )
            for row in rows
        ]
    def _predicate_hint_score(
        self,
        requested_predicate_iri: str,
        candidate_predicate_iri: str,
    ) -> float:
        requested = (
            self._local_name(requested_predicate_iri) or requested_predicate_iri
        ).lower()
        candidate = (
            self._local_name(candidate_predicate_iri) or candidate_predicate_iri
        ).lower()
        score = SequenceMatcher(None, requested, candidate).ratio()
        requested_tokens = self._predicate_hint_tokens(requested)
        candidate_tokens = self._predicate_hint_tokens(candidate)
        for requested_token in requested_tokens:
            for candidate_token in candidate_tokens:
                if requested_token == candidate_token:
                    score += 0.35
                elif (
                    len(requested_token) >= 5
                    and requested_token in candidate_token
                ) or (
                    len(candidate_token) >= 5
                    and candidate_token in requested_token
                ):
                    score += 0.25
        return score
    def _assertion_absence_note(
        self,
        matching_triples: list[ResourceTriple],
        same_subject_predicate_triples: list[ResourceTriple],
        requested_object: AssertionValue | None,
        predicate_hints: list[AssertionPredicateHint],
    ) -> str | None:
        if requested_object is None or matching_triples:
            return None
        requested_label = requested_object.value_label or requested_object.value
        if same_subject_predicate_triples:
            current_values = ", ".join(
                triple.object_label or triple.object
                for triple in same_subject_predicate_triples
            )
            return (
                f"Exact requested assertion for {requested_label} is absent, but "
                "the requested predicate is present on this subject. "
                "Current same-subject/predicate value(s): "
                f"{current_values}. Do not infer a replacement without inspecting "
                "these values and nearby lore."
            )
        hint_note = self._assertion_predicate_hint_note(predicate_hints)
        return (
            f"Exact requested assertion for {requested_label} is absent because "
            "the requested predicate is absent on this subject in the selected "
            f"graph.{hint_note}"
        )
    def _assertion_predicate_hint_note(
        self,
        predicate_hints: list[AssertionPredicateHint],
    ) -> str:
        if not predicate_hints:
            return ""
        labels = [
            hint.predicate_curie
            or hint.predicate_label
            or self._local_name(hint.predicate)
            or hint.predicate
            for hint in predicate_hints[:3]
        ]
        return (
            " Nearby predicates on the same subject include: "
            + ", ".join(labels)
            + "."
        )
    def _assertion_support_next_actions(
        self,
        subject_iri: str,
        predicate_iri: str,
        requested_object: AssertionValue | None,
        *,
        graph: str | None,
        dataset_context_iris: Iterable[str],
    ) -> list[SuggestedNextAction]:
        seeds = []
        dataset_seeds = list(dict.fromkeys(dataset_context_iris))
        seeds.extend(dataset_seeds)
        seeds.append(subject_iri)
        if requested_object is not None and requested_object.value_kind in {
            "iri",
            "blank_node",
        }:
            seeds.append(requested_object.value)
        seeds = list(dict.fromkeys(seeds))
        actions: list[SuggestedNextAction] = []

        def add_action(
            tool_name: str,
            arguments: dict[str, Any],
            reason: str,
        ) -> None:
            actions.append(
                SuggestedNextAction(
                    tool=f"doxabase.{tool_name}",
                    args=arguments,
                    reason=reason,
                )
            )

        add_action(
            "get_context_graph",
            {
                "seed_iris": seeds,
                "profile": "deep_lore",
            },
            (
                "Load a route-explained lore slice around the assertion target "
                "resources before making map changes."
            ),
        )
        for dataset_iri in dataset_seeds:
            add_action(
                "describe_dataset",
                {
                    "iri": dataset_iri,
                    "graph": None,
                },
                (
                    "Inspect the dataset context because assertion targets often "
                    "depend on table-level caveats, relationships, and layout facts."
                ),
            )
        add_action(
            "describe_resource",
            {
                "iri": subject_iri,
                "graph": None,
            },
            "Inspect all known triples directly attached to the assertion subject.",
        )
        if requested_object is not None:
            add_action(
                "describe_resource",
                {
                    "iri": subject_iri,
                    "aspect": "assertion_support",
                    "predicate": predicate_iri,
                    "object": None,
                    "graph": graph,
                },
                (
                    "Compare all current values for this subject/predicate, not "
                    "only the requested object."
                ),
            )
        if requested_object is not None and requested_object.value_kind in {
            "iri",
            "blank_node",
        }:
            add_action(
                "describe_resource",
                {
                    "iri": requested_object.value,
                    "graph": None,
                },
                "Inspect all known triples directly attached to the requested object.",
            )
        add_action(
            "search",
            {
                "query": self._local_name(predicate_iri) or predicate_iri,
                "graph": None,
            },
            (
                "Search for textual mentions of the predicate when route-based "
                "context is too sparse."
            ),
        )
        return actions
    def _assertion_related_lore_routes(
        self,
        target_iris: Iterable[str],
    ) -> list[AssertionSupportRoute]:
        targets = [
            iri
            for iri in dict.fromkeys(target_iris)
            if iri and not iri.startswith("_:")
        ]
        all_graphs = self._expand_graphs(["all"])
        pattern_graphs = self._expand_graphs(["patterns"])
        history_graphs = self._expand_graphs(["history"])
        lookup_graphs = self._lookup_graphs(all_graphs)

        description_predicates = {
            "observation": "rc:summary",
            "claim": "rc:claimText",
            "pattern": "rc:patternText",
            "evidence": "rc:summary",
            "revision": "rc:summary",
        }
        routes: list[AssertionSupportRoute] = []
        seen_routes: set[tuple[str, str, str, str | None]] = set()
        summary_cache: dict[tuple[str, str], ResourceSummary] = {}

        def summary(iri: str, kind: str) -> ResourceSummary:
            key = (iri, kind)
            if key not in summary_cache:
                summary_cache[key] = self._resource_summary(
                    lookup_graphs,
                    iri,
                    description_predicate=description_predicates.get(
                        kind,
                        "rdfs:comment",
                    ),
                    display_label=True,
                )
            return summary_cache[key]

        def add_route(
            resource_iri: str,
            resource_kind: str,
            route_type: str,
            route_label: str,
            matched_iri: str | None,
        ) -> None:
            key = (resource_kind, resource_iri, route_type, matched_iri)
            if key in seen_routes:
                return
            seen_routes.add(key)
            routes.append(
                AssertionSupportRoute(
                    resource=summary(resource_iri, resource_kind),
                    resource_kind=resource_kind,
                    route_type=route_type,
                    route_label=route_label,
                    matched_resource=(
                        summary(matched_iri, "matched_resource")
                        if matched_iri is not None
                        else None
                    ),
                )
            )

        observation_type = self.expand_iri("rc:Observation")
        claim_type = self.expand_iri("rc:Claim")
        pattern_type = self.expand_iri("rc:Pattern")
        evidence_type = self.expand_iri("rc:Evidence")

        for target_iri in targets:
            target_types = set(self._types_from_graphs(all_graphs, target_iri))
            if observation_type in target_types:
                add_route(
                    target_iri,
                    "observation",
                    "target_resource",
                    "target resource",
                    target_iri,
                )
            if claim_type in target_types:
                add_route(
                    target_iri,
                    "claim",
                    "target_resource",
                    "target resource",
                    target_iri,
                )
            if pattern_type in target_types:
                add_route(
                    target_iri,
                    "pattern",
                    "target_resource",
                    "target resource",
                    target_iri,
                )
            if evidence_type in target_types:
                add_route(
                    target_iri,
                    "evidence",
                    "target_resource",
                    "target resource",
                    target_iri,
                )

            for observation_iri in self._subjects(
                all_graphs,
                "rc:observedAsset",
                target_iri,
            ):
                add_route(
                    observation_iri,
                    "observation",
                    "observed_asset",
                    "observation observed asset",
                    target_iri,
                )
            for observation_iri in self._subjects(
                all_graphs,
                "rc:observedColumn",
                target_iri,
            ):
                add_route(
                    observation_iri,
                    "observation",
                    "observed_column",
                    "observation observed column",
                    target_iri,
                )
            for claim_iri in self._subjects(all_graphs, "rc:claimTarget", target_iri):
                add_route(
                    claim_iri,
                    "claim",
                    "claim_target",
                    "claim target",
                    target_iri,
                )
            for pattern_iri in self._subjects(
                pattern_graphs,
                "rc:patternTarget",
                target_iri,
            ):
                add_route(
                    pattern_iri,
                    "pattern",
                    "pattern_target",
                    "pattern target",
                    target_iri,
                )
            for pattern_iri in self._subjects(
                pattern_graphs,
                "rc:mapImplication",
                target_iri,
            ):
                add_route(
                    pattern_iri,
                    "pattern",
                    "map_implication",
                    "pattern map implication",
                    target_iri,
                )
            for revision_iri in self._subjects(
                history_graphs,
                "rc:revisionAnchor",
                target_iri,
            ):
                add_route(
                    revision_iri,
                    "revision",
                    "revision_anchor",
                    "revision anchor",
                    target_iri,
                )
            for evidence_iri in self._objects(all_graphs, target_iri, "rc:evidence"):
                add_route(
                    evidence_iri,
                    "evidence",
                    "target_evidence",
                    "target evidence",
                    target_iri,
                )

        observation_iris = [
            route.resource.iri
            for route in routes
            if route.resource_kind == "observation"
        ]
        for observation_iri in dict.fromkeys(observation_iris):
            for claim_iri in self._objects(all_graphs, observation_iri, "rc:hasClaim"):
                add_route(
                    claim_iri,
                    "claim",
                    "observation_claim",
                    "claim linked from observation",
                    observation_iri,
                )
            for evidence_iri in self._objects(all_graphs, observation_iri, "rc:evidence"):
                add_route(
                    evidence_iri,
                    "evidence",
                    "observation_evidence",
                    "evidence linked from observation",
                    observation_iri,
                )
            for pattern_iri in self._subjects(
                pattern_graphs,
                "rc:supportingObservation",
                observation_iri,
            ):
                add_route(
                    pattern_iri,
                    "pattern",
                    "supporting_observation",
                    "pattern supporting observation",
                    observation_iri,
                )
            for revision_iri in self._subjects(
                history_graphs,
                "rc:revisionSupportingObservation",
                observation_iri,
            ):
                add_route(
                    revision_iri,
                    "revision",
                    "revision_supporting_observation",
                    "revision supporting observation",
                    observation_iri,
                )

        claim_iris = [
            route.resource.iri
            for route in routes
            if route.resource_kind == "claim"
        ]
        for claim_iri in dict.fromkeys(claim_iris):
            for evidence_iri in self._objects(all_graphs, claim_iri, "rc:evidence"):
                add_route(
                    evidence_iri,
                    "evidence",
                    "claim_evidence",
                    "evidence linked from claim",
                    claim_iri,
                )
            for pattern_iri in self._subjects(
                pattern_graphs,
                "rc:supportingClaim",
                claim_iri,
            ):
                add_route(
                    pattern_iri,
                    "pattern",
                    "supporting_claim",
                    "pattern supporting claim",
                    claim_iri,
                )
            for revision_iri in self._subjects(
                history_graphs,
                "rc:revisionSupportingClaim",
                claim_iri,
            ):
                add_route(
                    revision_iri,
                    "revision",
                    "revision_supporting_claim",
                    "revision supporting claim",
                    claim_iri,
                )

        pattern_iris = [
            route.resource.iri
            for route in routes
            if route.resource_kind == "pattern"
        ]
        for pattern_iri in dict.fromkeys(pattern_iris):
            for evidence_iri in self._objects(all_graphs, pattern_iri, "rc:evidence"):
                add_route(
                    evidence_iri,
                    "evidence",
                    "pattern_evidence",
                    "evidence linked from pattern",
                    pattern_iri,
                )
            for revision_iri in self._subjects(
                history_graphs,
                "rc:revisionSupportingPattern",
                pattern_iri,
            ):
                add_route(
                    revision_iri,
                    "revision",
                    "revision_supporting_pattern",
                    "revision supporting pattern",
                    pattern_iri,
                )

        evidence_iris = [
            route.resource.iri
            for route in routes
            if route.resource_kind == "evidence"
        ]
        for evidence_iri in dict.fromkeys(evidence_iris):
            for revision_iri in self._subjects(history_graphs, "rc:evidence", evidence_iri):
                add_route(
                    revision_iri,
                    "revision",
                    "revision_evidence",
                    "revision evidence",
                    evidence_iri,
                )

        return routes
    def _assertion_related_route_summaries(
        self,
        routes: Iterable[AssertionSupportRoute],
        *,
        subject_iri: str,
    ) -> list[AssertionSupportRouteSummary]:
        route_groups: dict[tuple[str, str], list[AssertionSupportRoute]] = {}
        for route in routes:
            route_groups.setdefault(
                (route.resource_kind, route.resource.iri),
                [],
            ).append(route)

        route_weights = {
            "target_resource": 100,
            "claim_target": 90,
            "pattern_target": 88,
            "map_implication": 86,
            "observed_column": 84,
            "observed_asset": 80,
            "revision_anchor": 76,
            "target_evidence": 72,
            "observation_claim": 68,
            "supporting_observation": 64,
            "supporting_claim": 62,
            "observation_evidence": 58,
            "claim_evidence": 56,
            "pattern_evidence": 54,
            "revision_supporting_observation": 48,
            "revision_supporting_claim": 46,
            "revision_supporting_pattern": 44,
            "revision_evidence": 42,
        }
        kind_weights = {
            "claim": 6,
            "pattern": 5,
            "observation": 4,
            "evidence": 3,
            "revision": 2,
        }

        def route_weight(route: AssertionSupportRoute) -> int:
            return route_weights.get(route.route_type, 10)

        def route_kind_weight(route: AssertionSupportRoute) -> int:
            return kind_weights.get(route.resource_kind, 1)

        def unique_labels(group_routes: list[AssertionSupportRoute]) -> list[str]:
            return list(dict.fromkeys(route.route_label for route in group_routes))

        def unique_types(group_routes: list[AssertionSupportRoute]) -> list[str]:
            return list(dict.fromkeys(route.route_type for route in group_routes))

        def unique_matches(
            group_routes: list[AssertionSupportRoute],
        ) -> list[ResourceSummary]:
            matches: dict[str, ResourceSummary] = {}
            for route in group_routes:
                if route.matched_resource is not None:
                    matches.setdefault(
                        route.matched_resource.iri,
                        route.matched_resource,
                    )
            return list(matches.values())

        def route_note(
            *,
            resource: ResourceSummary,
            resource_kind: str,
            labels: list[str],
            matches: list[ResourceSummary],
            strongest_route: AssertionSupportRoute,
            relevance_tier: str,
        ) -> str:
            resource_label = resource.label or resource.iri
            label_text = ", ".join(labels)
            match_labels = [match.label or match.iri for match in matches]
            if match_labels:
                match_text = "; matches " + ", ".join(match_labels)
            else:
                match_text = ""
            return (
                f"{resource_label} ({resource_kind}): "
                f"{strongest_route.route_label}; "
                f"{len(labels)} route(s): {label_text}{match_text}. "
                f"Relevance tier: {relevance_tier}."
            )

        def generic_value_only(
            group_routes: list[AssertionSupportRoute],
            matches: list[ResourceSummary],
        ) -> bool:
            if not matches:
                return False
            if any(match.iri == subject_iri for match in matches):
                return False
            if not all(
                self._is_generic_shared_value_resource(match.iri)
                for match in matches
            ):
                return False
            route_types = {route.route_type for route in group_routes}
            resource_kinds = {route.resource_kind for route in group_routes}
            return resource_kinds == {"revision"} or route_types <= {
                "revision_anchor",
            }

        def route_relevance_tier(
            group_routes: list[AssertionSupportRoute],
            matches: list[ResourceSummary],
        ) -> str:
            if generic_value_only(group_routes, matches):
                return "generic_value_only"
            route_types = {route.route_type for route in group_routes}
            if "target_resource" in route_types or any(
                match.iri == subject_iri for match in matches
            ):
                return "direct"
            if route_types & {
                "claim_target",
                "pattern_target",
                "map_implication",
                "observed_column",
                "observed_asset",
                "revision_anchor",
                "target_evidence",
            }:
                return "target_support"
            return "linked_support"

        ranked_groups = sorted(
            route_groups.values(),
            key=lambda group: (
                -max(route_weight(route) for route in group),
                -max(route_kind_weight(route) for route in group),
                -len(group),
                (group[0].resource.label or group[0].resource.iri).lower(),
                group[0].resource.iri,
            ),
        )

        summaries: list[AssertionSupportRouteSummary] = []
        for rank, group in enumerate(ranked_groups, start=1):
            strongest_route = max(
                group,
                key=lambda route: (
                    route_weight(route),
                    route_kind_weight(route),
                    route.route_label,
                ),
            )
            labels = unique_labels(group)
            matches = unique_matches(group)
            relevance_tier = route_relevance_tier(group, matches)
            is_generic_value_only = generic_value_only(group, matches)
            summaries.append(
                AssertionSupportRouteSummary(
                    rank=rank,
                    resource=group[0].resource,
                    resource_kind=group[0].resource_kind,
                    route_count=len(group),
                    route_types=unique_types(group),
                    route_labels=labels,
                    matched_resources=matches,
                    strongest_route_type=strongest_route.route_type,
                    strongest_route_label=strongest_route.route_label,
                    relevance_tier=relevance_tier,
                    generic_value_only=is_generic_value_only,
                    route_note=route_note(
                        resource=group[0].resource,
                        resource_kind=group[0].resource_kind,
                        labels=labels,
                        matches=matches,
                        strongest_route=strongest_route,
                        relevance_tier=relevance_tier,
                    ),
                )
            )
        return summaries
    @staticmethod
    def _ordered_resource_summary_iris(
        summaries: Iterable[ResourceSummary],
    ) -> list[str]:
        return list(dict.fromkeys(summary.iri for summary in summaries))
    @staticmethod
    def _resource_triple_key(
        triple: ResourceTriple,
    ) -> tuple[str, str, str, str, str, str | None, str | None]:
        return (
            triple.graph,
            triple.subject,
            triple.predicate,
            triple.object,
            triple.object_kind,
            triple.object_datatype,
            triple.object_lang,
        )
    def _types(self, graph: str, subject: str) -> list[str]:
        return [
            row["object"]
            for row in self._conn.execute(
                """
                SELECT object
                FROM quads
                WHERE graph = ? AND subject = ? AND predicate = ?
                ORDER BY object
                """,
                (graph, subject, str(RDF.type)),
            )
        ]
    def _describe_analysis_denominator(
        self,
        denominator_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> AnalysisDenominatorDescription:
        return AnalysisDenominatorDescription(
            iri=denominator_iri,
            label=self._label_from_graphs(lookup_graphs, denominator_iri),
            description=self._first_object(
                data_graphs,
                denominator_iri,
                "rc:denominatorDescription",
            )
            or self._description_from_graphs(lookup_graphs, denominator_iri),
            row_count_snapshot=self._int_object(
                data_graphs,
                denominator_iri,
                "rc:denominatorRowCountSnapshot",
            ),
            basis=self._first_object(
                data_graphs,
                denominator_iri,
                "rc:denominatorBasis",
            ),
        )
    def _optional_resource_summary(
        self,
        graphs: list[str],
        iri: str | None,
    ) -> ResourceSummary | None:
        if iri is None:
            return None
        return self._resource_summary(graphs, iri)
    def _describe_transformation(
        self,
        transformation_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> TransformationDescription:
        return TransformationDescription(
            iri=transformation_iri,
            label=self._display_label_from_graphs(lookup_graphs, transformation_iri),
            description=self._description_from_graphs(lookup_graphs, transformation_iri),
            transformation_type=self._first_object(
                data_graphs,
                transformation_iri,
                "rc:transformationType",
            ),
            transformation_description=self._first_object(
                data_graphs,
                transformation_iri,
                "rc:transformationDescription",
            ),
        )
    def _describe_transform_condition(
        self,
        condition_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> TransformConditionDescription:
        condition_kind = self._first_object(
            data_graphs,
            condition_iri,
            "rc:conditionKind",
        )
        return TransformConditionDescription(
            iri=condition_iri,
            label=self._display_label_from_graphs(lookup_graphs, condition_iri),
            description=self._description_from_graphs(lookup_graphs, condition_iri),
            condition_kind=self._optional_resource_summary(
                lookup_graphs,
                condition_kind,
            ),
            expression=self._first_object(
                data_graphs,
                condition_iri,
                "rc:expressionText",
            ),
            expression_language=self._first_object(
                data_graphs,
                condition_iri,
                "rc:expressionLanguage",
            ),
            applies_to_datasets=self._resource_summaries(
                lookup_graphs,
                self._objects(data_graphs, condition_iri, "rc:appliesToDataset"),
            ),
            applies_to_endpoints=self._resource_summaries(
                lookup_graphs,
                self._objects(data_graphs, condition_iri, "rc:appliesToEndpoint"),
            ),
        )
    def _describe_transform_output(
        self,
        output_iri: str,
        relationship_conditions: Mapping[str, TransformConditionDescription],
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> TransformOutputDescription:
        target_dataset = self._first_object(data_graphs, output_iri, "rc:outputDataset")
        output_function = self._first_object(data_graphs, output_iri, "rc:outputFunction")
        condition_descriptions: list[TransformConditionDescription] = []
        for condition_iri in self._objects(data_graphs, output_iri, "rc:outputCondition"):
            condition_descriptions.append(
                relationship_conditions.get(condition_iri)
                or self._describe_transform_condition(
                    condition_iri,
                    data_graphs,
                    lookup_graphs,
                )
            )
        grain_iri = self._first_object(data_graphs, output_iri, "rc:outputGrain")
        return TransformOutputDescription(
            iri=output_iri,
            label=self._display_label_from_graphs(lookup_graphs, output_iri),
            description=self._description_from_graphs(lookup_graphs, output_iri),
            target_dataset=self._optional_resource_summary(
                lookup_graphs,
                target_dataset,
            ),
            role=self._first_object(data_graphs, output_iri, "rc:outputRole"),
            formula=self._first_object(data_graphs, output_iri, "rc:outputFormula"),
            expression_language=self._first_object(
                data_graphs,
                output_iri,
                "rc:expressionLanguage",
            ),
            function=self._optional_resource_summary(lookup_graphs, output_function),
            conditions=sorted(
                condition_descriptions,
                key=lambda condition: (condition.label or "", condition.iri),
            ),
            tuple_grain=(
                self._describe_tuple_grain(grain_iri, data_graphs, lookup_graphs)
                if grain_iri is not None
                else None
            ),
        )
    def _describe_tuple_grain(
        self,
        grain_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> TupleGrainDescription:
        components = [
            self._describe_grain_component(component_iri, data_graphs, lookup_graphs)
            for component_iri in self._objects(
                data_graphs,
                grain_iri,
                "rc:hasGrainComponent",
            )
        ]
        return TupleGrainDescription(
            iri=grain_iri,
            label=self._display_label_from_graphs(lookup_graphs, grain_iri),
            description=self._description_from_graphs(lookup_graphs, grain_iri),
            components=sorted(
                components,
                key=lambda component: (component.order or 999999, component.iri),
            ),
        )
    def _describe_grain_component(
        self,
        component_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> GrainComponentDescription:
        column_iri = self._first_object(data_graphs, component_iri, "rc:grainColumn")
        dataset_iri = self._first_object(data_graphs, component_iri, "rc:grainDataset")
        return GrainComponentDescription(
            iri=component_iri,
            label=self._display_label_from_graphs(lookup_graphs, component_iri),
            description=self._description_from_graphs(lookup_graphs, component_iri),
            order=self._int_object(data_graphs, component_iri, "rc:grainOrder"),
            role=self._first_object(data_graphs, component_iri, "rc:grainRole"),
            column=self._optional_resource_summary(lookup_graphs, column_iri),
            dataset=self._optional_resource_summary(lookup_graphs, dataset_iri),
            expression=self._first_object(data_graphs, component_iri, "rc:grainExpression"),
        )
    def _matched_resource_kind(self, graphs: list[str], iri: str) -> str | None:
        matched_type = self._first_matching_type(
            self._types_from_graphs(graphs, iri),
            [
                "rc:Table",
                "rc:Dataset",
                "rc:Column",
                "rc:KnownCaveat",
                "rc:ForeignKey",
                "rc:SharedIdentifier",
                "rc:Derivation",
                "rc:Claim",
                "rc:Observation",
                "rc:ProfileObservation",
                "rc:Evidence",
                "rc:SourceSpan",
            ],
        )
        return self._label_for_resource(matched_type)
    def _resource_summary(
        self,
        graphs: list[str],
        iri: str,
        *,
        description_predicate: str = "rdfs:comment",
        display_label: bool = False,
    ) -> ResourceSummary:
        column_name = self._first_object(graphs, iri, "rc:columnName")
        owning_dataset_iri = self._first_owner_dataset_iri(graphs, iri)
        label = (
            self._display_label_from_graphs(graphs, iri)
            if display_label
            else self._label_from_graphs(graphs, iri)
        )
        return ResourceSummary(
            iri=iri,
            label=label or column_name or self._local_name(iri),
            description=self._resource_description_from_graphs(
                graphs,
                iri,
                description_predicate=description_predicate,
            ),
            column_name=column_name,
            owning_dataset_iri=owning_dataset_iri,
            owning_dataset_label=(
                self._display_label_from_graphs(graphs, owning_dataset_iri)
                if owning_dataset_iri is not None
                else None
            ),
        )
    def _first_object(self, graphs: list[str], subject: str, predicate: str) -> str | None:
        objects = self._objects(graphs, subject, predicate)
        return objects[0] if objects else None
    def _int_object(self, graphs: list[str], subject: str, predicate: str) -> int | None:
        value = self._first_object(graphs, subject, predicate)
        return int(value) if value is not None else None
    def _resource_description_from_graphs(
        self,
        graphs: list[str],
        subject: str,
        *,
        description_predicate: str = "rdfs:comment",
    ) -> str | None:
        predicates = dict.fromkeys(
            [
                description_predicate,
                str(RDFS.comment),
                str(DCTERMS.description),
                "rc:caveatDescription",
                "rc:transformationDescription",
                "rc:sourceDescription",
                "rc:impact",
            ]
        )
        for predicate in predicates:
            description = self._first_object(graphs, subject, predicate)
            if description is not None:
                return description
        return self._synthesized_relationship_description_from_graphs(graphs, subject)
    def _compact_resource_label(self, graphs: list[str], subject: str) -> str:
        return (
            self._display_label_from_graphs(graphs, subject)
            or self._first_object(graphs, subject, "rc:columnName")
            or self._local_name(subject)
        )
    def _resource_summaries(
        self,
        graphs: list[str],
        iris: Iterable[str],
        *,
        description_predicate: str = "rdfs:comment",
    ) -> list[ResourceSummary]:
        return [
            self._resource_summary(
                graphs,
                iri,
                description_predicate=description_predicate,
                display_label=True,
            )
            for iri in iris
        ]
    def _describe_evidence(
        self,
        evidence_iri: str,
        graphs: list[str],
        lookup_graphs: list[str],
    ) -> EvidenceDescription:
        description = EvidenceDescription(
            iri=evidence_iri,
            label=self._display_label_from_graphs(lookup_graphs, evidence_iri),
            summary=self._first_object(graphs, evidence_iri, "rc:summary"),
            sources=list(
                dict.fromkeys(self._objects(graphs, evidence_iri, str(DCTERMS.source)))
            ),
            source_spans=self._sort_source_span_descriptions(
                [
                    self._describe_source_span(span_iri, graphs)
                    for span_iri in dict.fromkeys(
                        self._objects(graphs, evidence_iri, "rc:sourceSpan")
                    )
                ]
            ),
            scanned_source_handles=list(
                dict.fromkeys(
                    self._objects(graphs, evidence_iri, "rc:scannedSourceHandle")
                )
            ),
            query_execution_status=self._first_object(
                graphs,
                evidence_iri,
                "rc:queryExecutionStatus",
            ),
            query_engine=self._first_object(graphs, evidence_iri, "rc:queryEngine"),
            query_hash=self._first_object(graphs, evidence_iri, "rc:queryHash"),
        )
        return self._privacy_redacted_evidence_description(description)
    def _describe_source_span(
        self,
        source_span_iri: str,
        graphs: list[str],
    ) -> SourceSpanDescription:
        source_kind = self._first_object(graphs, source_span_iri, "rc:sourceKind")
        return SourceSpanDescription(
            iri=source_span_iri,
            source_path=self._first_object(graphs, source_span_iri, "rc:sourcePath"),
            source_section=self._first_object(
                graphs,
                source_span_iri,
                "rc:sourceSection",
            ),
            start_line=self._int_object(graphs, source_span_iri, "rc:startLine"),
            end_line=self._int_object(graphs, source_span_iri, "rc:endLine"),
            source_kind=source_kind,
            source_kind_label=self._label_for_resource(source_kind),
        )
    def _sort_source_span_descriptions(
        self,
        spans: Iterable[SourceSpanDescription],
    ) -> list[SourceSpanDescription]:
        priority_by_kind = {
            self.expand_iri("rc:QuerySource"): 0,
            self.expand_iri("rc:DataSampleSource"): 1,
        }
        return sorted(
            spans,
            key=lambda span: (
                priority_by_kind.get(span.source_kind or "", 2),
                span.source_path or "",
                span.source_section or "",
                span.start_line or 0,
                span.end_line or 0,
                span.iri,
            ),
        )
    def _label_for_resource(self, iri: str | None) -> str | None:
        if iri is None:
            return None
        return self._label_from_graphs(
            self._expand_graphs(["ontology"]),
            iri,
        ) or self._local_name(iri)
    def _resource_or_literal(self, value: str) -> Identifier:
        expanded = self.expand_iri(value)
        if "://" in expanded or expanded.startswith("urn:") or ":" in value:
            return URIRef(expanded)
        return Literal(value)
    def _controlled_resource_ref(
        self,
        name: str,
        value: str,
        allowed_values: Iterable[str],
    ) -> URIRef:
        ref = self._resource_ref(name, value)
        allowed = tuple(allowed_values)
        allowed_expanded = {self.expand_iri(item) for item in allowed}
        if str(ref) not in allowed_expanded:
            allowed_text = ", ".join(allowed)
            raise DoxaBaseError(f"{name} must be one of: {allowed_text}")
        return ref
    def _resource_ref(self, name: str, value: str) -> URIRef:
        text = value.strip()
        if not text:
            raise DoxaBaseError(f"{name} values must not be empty")
        if re.search(r"\s", text):
            raise DoxaBaseError(
                f"{name} values must be IRIs or CURIEs, not prose: {value!r}"
            )
        expanded = self.expand_iri(text)
        if "://" not in expanded and not expanded.startswith("urn:") and ":" not in text:
            if self._is_relationship_column_ref_name(name):
                raise DoxaBaseError(
                    f"{name} values must be recorded column IRIs or CURIEs, "
                    f"not raw column names: {value!r}. Record the column first "
                    "with record_map_column, then pass the column IRI in "
                    "relationship column fields."
                )
            if name == "compression_codec":
                raise DoxaBaseError(
                    f"{name} values must be IRIs or CURIEs, not plain names: "
                    f"{value!r}. Use a canonical compression CURIE such as "
                    "'rc:ZstdCompression', 'rc:SnappyCompression', or "
                    "'rc:GzipCompression', or a full project IRI."
                )
            raise DoxaBaseError(
                f"{name} values must be IRIs or CURIEs, not plain names: "
                f"{value!r}. Use a CURIE such as 'rc:Moderate' or 'rc:Varchar', "
                "or a full project IRI."
            )
        return URIRef(expanded)
    def _resource_triples(
        self,
        graphs: list[str],
        *,
        subject: str | None = None,
        object_value: str | None = None,
        object_kind: str | None = None,
        limit: int | None = 100,
        offset: int = 0,
    ) -> list[ResourceTriple]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        filters: list[str] = []
        params: list[Any] = []
        if subject is not None:
            filters.append("q.subject = ?")
            params.append(subject)
        if object_value is not None:
            filters.append("q.object = ?")
            params.append(object_value)
        if object_kind is not None:
            filters.append("q.object_kind = ?")
            params.append(object_kind)
        if not filters:
            raise DoxaBaseError("Resource triple lookup requires subject or object")
        where = " AND ".join(filters)
        limit_clause = ""
        limit_params: list[Any] = []
        if limit is not None:
            limit_clause = "LIMIT ? OFFSET ?"
            limit_params.extend([limit, offset])
        rows = self._conn.execute(
            f"""
            SELECT
                q.graph,
                q.subject,
                q.subject_kind,
                q.predicate,
                q.object,
                q.object_kind,
                q.datatype,
                q.lang
            FROM quads q
            WHERE {where}
              {graph_filter}
            ORDER BY q.graph, q.subject, q.predicate, q.object
            {limit_clause}
            """,
            [*params, *graph_params, *limit_params],
        ).fetchall()
        return [self._resource_triple_from_row(row) for row in rows]
    def _resource_triple_count(
        self,
        graphs: list[str],
        *,
        subject: str | None = None,
        object_value: str | None = None,
        object_kind: str | None = None,
    ) -> int:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        filters: list[str] = []
        params: list[Any] = []
        if subject is not None:
            filters.append("q.subject = ?")
            params.append(subject)
        if object_value is not None:
            filters.append("q.object = ?")
            params.append(object_value)
        if object_kind is not None:
            filters.append("q.object_kind = ?")
            params.append(object_kind)
        if not filters:
            raise DoxaBaseError("Resource triple count requires subject or object")
        where = " AND ".join(filters)
        row = self._conn.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM quads q
            WHERE {where}
              {graph_filter}
            """,
            [*params, *graph_params],
        ).fetchone()
        return int(row["count"])
    def _resource_blank_node_objects(
        self,
        graphs: list[str],
        *,
        subject: str,
    ) -> list[str]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        rows = self._conn.execute(
            f"""
            SELECT DISTINCT q.object
            FROM quads q
            WHERE q.subject = ?
              AND q.object_kind = 'bnode'
              {graph_filter}
            ORDER BY q.object
            """,
            [subject, *graph_params],
        ).fetchall()
        return [row["object"] for row in rows]
    def _resource_blank_node_closure(
        self,
        graphs: list[str],
        *,
        subject: str,
        max_depth: int,
        limit: int,
    ) -> tuple[list[ResourceTriple], int, bool, int]:
        if max_depth == 0:
            frontier = self._resource_blank_node_objects(graphs, subject=subject)
            return [], 0, bool(frontier), len(frontier)
        frontier = self._resource_blank_node_objects(graphs, subject=subject)
        visited: set[str] = set()
        seen_triples: set[
            tuple[str, str, str, str, str, str | None, str | None]
        ] = set()
        closure_triples: list[ResourceTriple] = []
        for _depth in range(max_depth):
            if not frontier:
                break
            next_frontier: list[str] = []
            for blank_node in frontier:
                if blank_node in visited:
                    continue
                visited.add(blank_node)
                triples = self._resource_triples(
                    graphs,
                    subject=blank_node,
                    limit=None,
                )
                for triple in triples:
                    triple_key = (
                        triple.graph,
                        triple.subject,
                        triple.predicate,
                        triple.object,
                        triple.object_kind,
                        triple.object_datatype,
                        triple.object_lang,
                    )
                    if triple_key in seen_triples:
                        continue
                    seen_triples.add(triple_key)
                    closure_triples.append(triple)
                    if (
                        triple.object_kind == "bnode"
                        and triple.object not in visited
                        and triple.object not in next_frontier
                    ):
                        next_frontier.append(triple.object)
            frontier = next_frontier
        total_count = len(closure_triples)
        unvisited = [blank_node for blank_node in frontier if blank_node not in visited]
        return closure_triples[:limit], total_count, bool(unvisited), len(unvisited)
    def _assertion_triples(
        self,
        graphs: list[str],
        *,
        subject: str,
        predicate: str,
        object_filter: tuple[str, str, str | None, str | None] | None,
        limit: int,
    ) -> list[ResourceTriple]:
        graph_filter, graph_params = self._graph_filter(graphs, alias="q")
        filters = ["q.subject = ?", "q.predicate = ?"]
        params: list[Any] = [subject, predicate]
        if object_filter is not None:
            object_value, object_kind, datatype, lang = object_filter
            filters.extend(
                [
                    "q.object = ?",
                    "q.object_kind = ?",
                    "q.datatype IS ?",
                    "q.lang IS ?",
                ]
            )
            params.extend([object_value, object_kind, datatype, lang])
        where = " AND ".join(filters)
        rows = self._conn.execute(
            f"""
            SELECT
                q.graph,
                q.subject,
                q.subject_kind,
                q.predicate,
                q.object,
                q.object_kind,
                q.datatype,
                q.lang
            FROM quads q
            WHERE {where}
              {graph_filter}
            ORDER BY q.graph, q.subject, q.predicate, q.object
            LIMIT ?
            """,
            [*params, *graph_params, limit],
        ).fetchall()
        return [self._resource_triple_from_row(row) for row in rows]
    def _resource_triple_from_row(self, row: sqlite3.Row) -> ResourceTriple:
        lookup_graphs = self._lookup_graphs([row["graph"]])
        object_is_resource = row["object_kind"] in {"uri", "bnode"}
        return ResourceTriple(
            graph=row["graph"],
            subject=row["subject"],
            subject_kind=row["subject_kind"],
            subject_label=self._display_label_from_graphs(
                lookup_graphs,
                row["subject"],
            ),
            subject_types=self._types_from_graphs(lookup_graphs, row["subject"]),
            predicate=row["predicate"],
            predicate_label=self._label_from_graphs(
                self._expand_graphs(["ontology"]),
                row["predicate"],
            ),
            object=row["object"],
            object_kind=row["object_kind"],
            object_label=(
                self._display_label_from_graphs(lookup_graphs, row["object"])
                if object_is_resource
                else None
            ),
            object_types=(
                self._types_from_graphs(lookup_graphs, row["object"])
                if object_is_resource
                else []
            ),
            object_datatype=row["datatype"],
            object_lang=row["lang"],
        )
