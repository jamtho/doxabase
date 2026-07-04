"""Dataset and analysis-view description.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via DatasetsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class DatasetsMixin:
    def _dataset_description_is_table(self, dataset: DatasetDescription) -> bool:
        return self.expand_iri("rc:Table") in dataset.types
    def describe_dataset(self, iri: str, graph: str | None = "map") -> DatasetDescription:
        dataset_iri = self.expand_iri(iri)
        data_graphs = self._expand_graphs([graph] if graph else None)
        lookup_graphs = self._lookup_graphs(data_graphs)
        if not self._subject_exists(dataset_iri, data_graphs):
            graph_label = graph if graph is not None else "all graphs"
            raise DoxaBaseError(
                f"Dataset '{iri}' was not found in {graph_label}"
                f"{self._missing_dataset_profile_hint(dataset_iri, iri)}"
            )

        columns = [
            self._describe_column(column_iri, data_graphs, lookup_graphs)
            for column_iri in self._objects(data_graphs, dataset_iri, "rc:hasColumn")
        ]
        columns.sort(key=lambda column: (column.column_name or "", column.iri))
        column_iris = [column.iri for column in columns]

        physical_layouts = [
            self._describe_physical_layout(layout_iri, data_graphs, lookup_graphs)
            for layout_iri in self._objects(data_graphs, dataset_iri, "rc:hasPhysicalLayout")
        ]
        storage_accesses = [
            self._describe_storage_access(access_iri, data_graphs, lookup_graphs)
            for access_iri in self._objects(data_graphs, dataset_iri, "rc:hasStorageAccess")
        ]
        partition_schemes = [
            self._describe_partition(partition_iri, data_graphs, lookup_graphs)
            for partition_iri in self._objects(data_graphs, dataset_iri, "rc:partitionedBy")
        ]
        direct_path_templates = self._objects(data_graphs, dataset_iri, "rc:pathTemplate")
        access_path_templates = [
            path_template
            for storage_access in storage_accesses
            for path_template in storage_access.path_templates
        ]
        partition_path_templates = [
            partition.path_template
            for partition in partition_schemes
            if partition.path_template is not None
        ]
        path_templates = list(
            dict.fromkeys(
                direct_path_templates + partition_path_templates + access_path_templates
            )
        )
        caveat_iris = self._objects(data_graphs, dataset_iri, "rc:hasKnownCaveat")
        provenance_iris = self._objects(data_graphs, dataset_iri, "rc:hasProvenance")
        relationships = self._relationships_for_dataset(
            dataset_iri,
            column_iris,
            data_graphs,
            lookup_graphs,
        )
        tuple_grains = self._tuple_grains_for_dataset(
            dataset_iri,
            data_graphs,
            lookup_graphs,
        )
        linked_pattern_targets = [
            dataset_iri,
            *column_iris,
            *caveat_iris,
            *(relationship.iri for relationship in relationships),
            *(grain.iri for grain in tuple_grains),
            *(
                component.iri
                for grain in tuple_grains
                for component in grain.components
            ),
        ]
        related_datasets = self._related_datasets(
            dataset_iri,
            data_graphs,
            lookup_graphs,
            relationships=relationships,
        )
        linked_pattern_reasons = self._linked_pattern_reasons_for_dataset(
            linked_pattern_targets,
        )
        caveats = [
            self._describe_caveat(caveat_iri, data_graphs, lookup_graphs)
            for caveat_iri in caveat_iris
        ]
        profile_observations = self._profile_observations_for_target(
            target_iri=dataset_iri,
            target_predicate="rc:observedAsset",
            exclude_observed_column=True,
        )
        unmapped_column_profile_observations = (
            self._unmapped_column_profile_observations_for_dataset(
                dataset_iri,
                mapped_column_iris=column_iris,
            )
        )
        total_dataset_profile_count = self._profile_observation_count_for_target(
            target_iri=dataset_iri,
            target_predicate="rc:observedAsset",
            exclude_observed_column=True,
        )
        total_mapped_column_profile_count = sum(
            self._profile_observation_count_for_target(
                target_iri=column_iri,
                target_predicate="rc:observedColumn",
            )
            for column_iri in column_iris
        )
        total_unmapped_column_profile_count = (
            self._unmapped_column_profile_observation_count_for_dataset(
                dataset_iri,
                mapped_column_iris=column_iris,
            )
        )

        row_count_snapshot = self._int_object(
            data_graphs,
            dataset_iri,
            "rc:rowCountSnapshot",
        )
        description = DatasetDescription(
            iri=dataset_iri,
            graph=graph,
            label=self._label_from_graphs(lookup_graphs, dataset_iri),
            description=self._description_from_graphs(lookup_graphs, dataset_iri),
            types=self._types_from_graphs(data_graphs, dataset_iri),
            row_semantics=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(data_graphs, dataset_iri, "rc:rowSemantics"),
            ),
            entity_key=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(data_graphs, dataset_iri, "rc:entityKey"),
            ),
            snapshot_timestamp=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(data_graphs, dataset_iri, "rc:snapshotTimestamp"),
            ),
            schema_stability=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(data_graphs, dataset_iri, "rc:schemaStability"),
            ),
            row_count_snapshot=row_count_snapshot,
            layout_verification_status=self._optional_resource_summary(
                lookup_graphs,
                self._first_object(
                    data_graphs,
                    dataset_iri,
                    "rc:layoutVerificationStatus",
                ),
            ),
            layout_verification_note=self._first_object(
                data_graphs,
                dataset_iri,
                "rc:layoutVerificationNote",
            ),
            profile_summary=self._profile_summary(
                profile_observations,
                columns,
                unmapped_column_profile_observations,
                total_dataset_profile_count=total_dataset_profile_count,
                total_mapped_column_profile_count=(
                    total_mapped_column_profile_count
                ),
                total_unmapped_column_profile_count=(
                    total_unmapped_column_profile_count
                ),
                row_count_snapshot=row_count_snapshot,
            ),
            profile_observations=profile_observations,
            unmapped_column_profile_observations=unmapped_column_profile_observations,
            columns=columns,
            path_templates=path_templates,
            physical_layouts=physical_layouts,
            storage_accesses=storage_accesses,
            partition_schemes=partition_schemes,
            caveats=caveats,
            upstream_caveats=self._upstream_caveats_for_dataset(
                caveat_iris,
                relationships,
            ),
            operational_warnings=[],
            provenance=[
                self._resource_summary(
                    lookup_graphs,
                    provenance_iri,
                    description_predicate="rc:sourceDescription",
                )
                for provenance_iri in provenance_iris
            ],
            transformations=self._transformations_for_provenance(
                provenance_iris,
                data_graphs,
                lookup_graphs,
            ),
            related_datasets=related_datasets,
            related_dataset_groups=self._related_dataset_groups(
                dataset_iri,
                related_datasets,
                relationships,
            ),
            relationships=relationships,
            tuple_grains=tuple_grains,
            linked_patterns=self._linked_patterns_for_dataset(
                linked_pattern_targets,
            ),
            linked_pattern_reasons=linked_pattern_reasons,
        )
        return replace(
            description,
            operational_warnings=self._query_planning_issues(description),
        )
    def _validate_dataset_endpoint_resources(
        self,
        fields: Iterable[tuple[str, str]],
    ) -> None:
        for field_name, value in fields:
            self._validate_dataset_endpoint_resource(field_name, value)
    def _validate_dataset_endpoint_resource(
        self,
        field_name: str,
        value: str,
    ) -> None:
        endpoint_iri = str(self._resource_ref(field_name, value))
        resource_types = set(
            self._types_from_graphs(self._expand_graphs(["all"]), endpoint_iri)
        )
        if self.expand_iri("rc:Column") not in resource_types:
            return
        raise DoxaBaseError(
            f"{field_name} points to a recorded rc:Column, not a data asset "
            f"endpoint: {endpoint_iri}. Use source_columns/derived_columns for "
            "column derivations such as body -> body_top; "
            "record_map_asset_transform dataset endpoints and outputs are for "
            "data assets."
        )
    def _normalise_aggregated_column_specs(
        self,
        value: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if value is None:
            return []
        if isinstance(value, Mapping):
            raw_items = [value]
        elif isinstance(value, str):
            raise DoxaBaseError(
                "aggregated_columns must be an object or list of objects"
            )
        else:
            raw_items = list(value)

        normalised: list[dict[str, Any]] = []
        for index, item in enumerate(raw_items, start=1):
            if not isinstance(item, Mapping):
                raise DoxaBaseError("aggregated_columns entries must be objects")
            target_column = str(
                item.get("target_column")
                or item.get("targetColumn")
                or ""
            ).strip()
            if not target_column:
                raise DoxaBaseError(
                    f"aggregated_columns[{index}] requires target_column"
                )
            source_columns = self._string_values(
                f"aggregated_columns[{index}].source_columns",
                item.get("source_columns")
                or item.get("sourceColumns")
                or item.get("aggregation_source_columns")
                or item.get("aggregationSourceColumns")
                or item.get("source_column")
                or item.get("aggregationSourceColumn"),
            )
            if not source_columns:
                raise DoxaBaseError(
                    f"aggregated_columns[{index}] requires source_columns"
                )
            normalised.append(
                {
                    "iri": str(item.get("iri") or item.get("id") or "").strip()
                    or None,
                    "target_column": target_column,
                    "source_columns": source_columns,
                    "aggregation_function": str(
                        item.get("aggregation_function")
                        or item.get("aggregationFunction")
                        or item.get("function")
                        or ""
                    ).strip()
                    or None,
                    "within_group_ordering": str(
                        item.get("within_group_ordering")
                        or item.get("withinGroupOrdering")
                        or item.get("ordering")
                        or ""
                    ).strip()
                    or None,
                }
            )
        return normalised
    def _delete_existing_aggregated_column_triples(self, relationship_iri: str) -> None:
        mapping_iris = self._objects(["map"], relationship_iri, "rc:hasAggregatedColumn")
        if not mapping_iris:
            return
        predicates = [
            str(RDF.type),
            self.expand_iri("rc:targetColumn"),
            self.expand_iri("rc:aggregationSourceColumn"),
            self.expand_iri("rc:aggregationFunction"),
            self.expand_iri("rc:withinGroupOrdering"),
        ]
        placeholders = ",".join("?" for _ in predicates)
        for mapping_iri in mapping_iris:
            self._conn.execute(
                f"""
                DELETE FROM quads
                WHERE graph = ?
                  AND subject = ?
                  AND predicate IN ({placeholders})
                """,
                ["map", mapping_iri, *predicates],
            )
        self._conn.commit()
    def _assertion_dataset_context_iris(
        self,
        lookup_graphs: list[str],
        target_resources: Iterable[ResourceSummary],
    ) -> list[str]:
        dataset_types = {
            self.expand_iri("rc:Dataset"),
            self.expand_iri("rc:Table"),
        }
        dataset_iris: list[str] = []
        for resource in target_resources:
            if (
                set(self._types_from_graphs(lookup_graphs, resource.iri))
                & dataset_types
            ):
                dataset_iris.append(resource.iri)
            if resource.owning_dataset_iri is not None:
                dataset_iris.append(resource.owning_dataset_iri)
        return list(dict.fromkeys(dataset_iris))
    def _markdown_table_cell(self, value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")
    def to_dataset(
        self,
        graphs: Iterable[str] | str | None = None,
        *,
        graph_iri_prefix: str = RCG_PREFIX,
    ) -> Dataset:
        dataset = Dataset()
        for prefix, namespace in PREFIXES.items():
            dataset.bind(prefix, namespace)
        dataset.bind("rcg", graph_iri_prefix)
        graph_names = self._graph_names_for_export(
            graphs,
            default_preset="all_with_seeds",
        )
        params: list[Any] = []
        graph_filter = ""
        if graph_names:
            graph_filter = f"WHERE graph IN ({','.join('?' for _ in graph_names)})"
            params.extend(graph_names)
        for row in self._conn.execute(
            f"""
            SELECT graph, subject, subject_kind, predicate, object, object_kind, datatype, lang
            FROM quads
            {graph_filter}
            """,
            params,
        ):
            context = dataset.graph(
                URIRef(self._export_graph_identifier(row["graph"], graph_iri_prefix))
            )
            context.add(
                (
                    self._term_from_row(row["subject"], row["subject_kind"]),
                    URIRef(row["predicate"]),
                    self._object_from_row(row),
                )
            )
        return dataset
    def _ensure_mutable(self, graph: str, *, allow_immutable: bool = False) -> None:
        row = self._conn.execute(
            "SELECT mutable FROM named_graphs WHERE name = ?",
            (graph,),
        ).fetchone()
        if row is not None and not bool(row["mutable"]) and not allow_immutable:
            raise ImmutableGraphError(f"Graph '{graph}' is immutable")
    def _parse_rdf_dataset(
        self,
        source: str | Path,
        *,
        format: str,
        parser_context: str,
    ) -> Dataset:
        dataset = Dataset()
        path = _existing_path(source)
        try:
            if path is not None:
                dataset.parse(path, format=format)
            else:
                dataset.parse(data=str(source), format=format)
        except Exception as exc:
            detail = self._rdf_parse_error_detail(exc)
            raise DoxaBaseError(
                f"Could not parse {parser_context} source as {format}: {detail}"
            ) from exc
        return dataset
    def _describe_column(
        self,
        column_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> ColumnDescription:
        physical_type = self._first_object(data_graphs, column_iri, "rc:physicalType")
        value_type = self._first_object(data_graphs, column_iri, "rc:valueType")
        return ColumnDescription(
            iri=column_iri,
            label=self._label_from_graphs(lookup_graphs, column_iri),
            description=self._description_from_graphs(lookup_graphs, column_iri),
            column_name=self._first_object(data_graphs, column_iri, "rc:columnName"),
            physical_type=(
                self._resource_summary(lookup_graphs, physical_type)
                if physical_type is not None
                else None
            ),
            value_type=(
                self._resource_summary(lookup_graphs, value_type)
                if value_type is not None
                else None
            ),
            nullable=self._bool_object(data_graphs, column_iri, "rc:nullable"),
            profile_observations=self._profile_observations_for_target(
                target_iri=column_iri,
                target_predicate="rc:observedColumn",
            ),
        )
    def _related_datasets(
        self,
        dataset_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
        *,
        relationships: Iterable[RelationshipDescription] = (),
    ) -> list[RelatedDatasetDescription]:
        related: list[RelatedDatasetDescription] = []
        for companion_iri in self._objects(data_graphs, dataset_iri, "rc:companionOf"):
            related.append(
                self._related_dataset(
                    companion_iri,
                    "companion",
                    None,
                    lookup_graphs,
                )
            )
        for companion_iri in self._subjects(data_graphs, "rc:companionOf", dataset_iri):
            related.append(
                self._related_dataset(
                    companion_iri,
                    "companion",
                    None,
                    lookup_graphs,
                )
            )

        for relationship_iri in self._subjects(data_graphs, "rc:sourceDataset", dataset_iri):
            relationship_direction = self._dataset_endpoint_relationship_direction(
                relationship_iri,
                lookup_graphs,
                source_side=True,
            )
            for target_iri in self._objects(data_graphs, relationship_iri, "rc:targetDataset"):
                related.append(
                    self._related_dataset(
                        target_iri,
                        relationship_direction,
                        relationship_iri,
                        lookup_graphs,
                    )
                )
        for relationship_iri in self._subjects(data_graphs, "rc:targetDataset", dataset_iri):
            relationship_direction = self._dataset_endpoint_relationship_direction(
                relationship_iri,
                lookup_graphs,
                source_side=False,
            )
            for source_iri in self._objects(data_graphs, relationship_iri, "rc:sourceDataset"):
                related.append(
                    self._related_dataset(
                        source_iri,
                        relationship_direction,
                        relationship_iri,
                        lookup_graphs,
                    )
                )
        for relationship in relationships:
            related.extend(
                self._related_datasets_from_column_relationship(
                    dataset_iri,
                    relationship,
                    lookup_graphs,
                )
            )
        return list(
            {
                (
                    item.iri,
                    item.relationship,
                    item.relationship_iri,
                ): item
                for item in related
            }.values()
        )
    def _related_dataset(
        self,
        iri: str,
        relationship: str,
        relationship_iri: str | None,
        lookup_graphs: list[str],
    ) -> RelatedDatasetDescription:
        summary = self._resource_summary(lookup_graphs, iri)
        relationship_types = (
            self._types_from_graphs(lookup_graphs, relationship_iri)
            if relationship_iri is not None
            else []
        )
        relationship_kind = self._first_matching_type(
            relationship_types,
            [
                "rc:ForeignKey",
                "rc:SharedIdentifier",
                "rc:Derivation",
                "rc:Aggregation",
                "rc:Relationship",
            ],
        )
        return RelatedDatasetDescription(
            iri=summary.iri,
            label=summary.label,
            description=summary.description,
            relationship=relationship,
            relationship_iri=relationship_iri,
            relationship_label=(
                self._display_label_from_graphs(lookup_graphs, relationship_iri)
                if relationship_iri is not None
                else None
            ),
            relationship_kind=relationship_kind,
            relationship_kind_label=self._label_for_resource(relationship_kind),
        )
    def _related_dataset_groups(
        self,
        dataset_iri: str,
        related_datasets: Iterable[RelatedDatasetDescription],
        relationships: Iterable[RelationshipDescription],
    ) -> list[RelatedDatasetGroup]:
        relationships_by_iri = {
            relationship.iri: relationship
            for relationship in relationships
        }
        groups: dict[str, RelatedDatasetDescription] = {}
        reasons_by_group: dict[
            str,
            dict[tuple[tuple[str, ...], tuple[str, ...]], list[RelatedDatasetReasonTag]],
        ] = {}
        columns_by_reason: dict[
            tuple[str, tuple[tuple[str, ...], tuple[str, ...]]],
            tuple[list[ResourceSummary], list[ResourceSummary], list[ResourceSummary]],
        ] = {}
        source_caveats_by_reason: dict[
            tuple[str, tuple[tuple[str, ...], tuple[str, ...]]],
            dict[str, CaveatDescription],
        ] = {}
        seen_tags: set[tuple[str, str, str | None]] = set()

        for related in related_datasets:
            groups.setdefault(related.iri, related)
            reasons_by_group.setdefault(related.iri, {})

            tag_key = (related.iri, related.relationship, related.relationship_iri)
            if tag_key in seen_tags:
                continue
            seen_tags.add(tag_key)
            relationship = (
                relationships_by_iri.get(related.relationship_iri)
                if related.relationship_iri is not None
                else None
            )
            columns = (
                self._relationship_columns_between_datasets(
                    dataset_iri,
                    related.iri,
                    relationship,
                )
                if relationship is not None
                else []
            )
            current_columns = [
                column
                for column in columns
                if column.owning_dataset_iri == dataset_iri
            ]
            related_columns = [
                column
                for column in columns
                if column.owning_dataset_iri == related.iri
            ]
            reason_key = (
                tuple(column.iri for column in current_columns),
                tuple(column.iri for column in related_columns),
            )
            reasons_by_group[related.iri].setdefault(reason_key, [])
            columns_by_reason[(related.iri, reason_key)] = (
                columns,
                current_columns,
                related_columns,
            )
            source_caveats_by_reason.setdefault((related.iri, reason_key), {})
            if relationship is not None:
                source_caveats_by_reason[(related.iri, reason_key)].update(
                    {
                        caveat.iri: caveat
                        for caveat in relationship.source_caveats
                    }
                )
            reasons_by_group[related.iri][reason_key].append(
                RelatedDatasetReasonTag(
                    relationship=related.relationship,
                    relationship_iri=related.relationship_iri,
                    relationship_label=related.relationship_label,
                    relationship_kind=related.relationship_kind,
                    relationship_kind_label=related.relationship_kind_label,
                    declared=relationship.declared if relationship is not None else None,
                    referential_integrity=(
                        relationship.referential_integrity
                        if relationship is not None
                        else None
                    ),
                )
            )

        return [
            RelatedDatasetGroup(
                iri=related.iri,
                label=related.label,
                description=related.description,
                reasons=sorted(
                    [
                        self._related_dataset_reason(
                            reason_tags,
                            *columns_by_reason[(related.iri, reason_key)],
                            list(
                                source_caveats_by_reason[
                                    (related.iri, reason_key)
                                ].values()
                            ),
                        )
                        for reason_key, reason_tags in reasons_by_group[
                            related.iri
                        ].items()
                    ],
                    key=self._related_dataset_reason_sort_key,
                ),
            )
            for related in sorted(
                groups.values(),
                key=lambda item: (item.label or "", item.iri),
            )
        ]
    def _related_dataset_reason(
        self,
        tags: list[RelatedDatasetReasonTag],
        columns: list[ResourceSummary],
        current_dataset_columns: list[ResourceSummary],
        related_dataset_columns: list[ResourceSummary],
        source_caveats: list[CaveatDescription],
    ) -> RelatedDatasetReason:
        sorted_tags = sorted(tags, key=self._related_dataset_reason_tag_sort_key)
        primary = sorted_tags[0]
        return RelatedDatasetReason(
            relationship=primary.relationship,
            relationship_iri=primary.relationship_iri,
            relationship_label=primary.relationship_label,
            relationship_kind=primary.relationship_kind,
            relationship_kind_label=primary.relationship_kind_label,
            columns=columns,
            current_dataset_columns=current_dataset_columns,
            related_dataset_columns=related_dataset_columns,
            declared=primary.declared,
            referential_integrity=primary.referential_integrity,
            source_caveats=sorted(
                source_caveats,
                key=lambda caveat: (caveat.label or "", caveat.iri),
            ),
            relationship_tags=sorted_tags,
        )
    def _related_dataset_reason_sort_key(
        self,
        reason: RelatedDatasetReason,
    ) -> tuple[int, str, str]:
        return (
            self._relationship_kind_priority(reason.relationship_kind),
            reason.relationship_label or "",
            reason.relationship,
        )
    def _related_dataset_reason_tag_sort_key(
        self,
        tag: RelatedDatasetReasonTag,
    ) -> tuple[int, str, str]:
        return (
            self._relationship_kind_priority(tag.relationship_kind),
            tag.relationship_label or "",
            tag.relationship,
        )
    def _transformations_for_provenance(
        self,
        provenance_iris: Iterable[str],
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> list[TransformationDescription]:
        transformation_iris: list[str] = []
        for provenance_iri in provenance_iris:
            transformation_iris.extend(
                self._objects(data_graphs, provenance_iri, "rc:hasTransformation")
            )
        return [
            self._describe_transformation(transformation_iri, data_graphs, lookup_graphs)
            for transformation_iri in dict.fromkeys(transformation_iris)
        ]
    def _describe_aggregated_column(
        self,
        aggregated_column_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> AggregatedColumnDescription:
        target_column = self._first_object(
            data_graphs,
            aggregated_column_iri,
            "rc:targetColumn",
        )
        aggregation_function = self._first_object(
            data_graphs,
            aggregated_column_iri,
            "rc:aggregationFunction",
        )
        within_group_ordering = self._first_object(
            data_graphs,
            aggregated_column_iri,
            "rc:withinGroupOrdering",
        )
        return AggregatedColumnDescription(
            iri=aggregated_column_iri,
            target_column=self._optional_resource_summary(
                lookup_graphs,
                target_column,
            ),
            source_columns=self._resource_summaries(
                lookup_graphs,
                self._objects(
                    data_graphs,
                    aggregated_column_iri,
                    "rc:aggregationSourceColumn",
                ),
            ),
            aggregation_function=self._optional_resource_summary(
                lookup_graphs,
                aggregation_function,
            ),
            within_group_ordering=self._optional_resource_summary(
                lookup_graphs,
                within_group_ordering,
            ),
        )
    def _tuple_grains_for_dataset(
        self,
        dataset_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> list[TupleGrainDescription]:
        grain_iris = list(self._objects(data_graphs, dataset_iri, "rc:hasGrain"))
        for output_iri in self._subjects(data_graphs, "rc:outputDataset", dataset_iri):
            grain_iris.extend(self._objects(data_graphs, output_iri, "rc:outputGrain"))
        return [
            self._describe_tuple_grain(grain_iri, data_graphs, lookup_graphs)
            for grain_iri in sorted(set(grain_iris))
        ]
    def _first_owner_dataset_iri(self, graphs: list[str], iri: str) -> str | None:
        return self._first_subject(graphs, "rc:hasColumn", iri)
    def _normalise_table_bundle_column_specs(
        self,
        dataset_iri: str,
        columns: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        if columns is None:
            column_values: list[Mapping[str, Any]] = []
        elif isinstance(columns, MappingABC):
            column_values = [columns]
        else:
            column_values = list(columns)
        allowed_fields = {
            "iri",
            "column_iri",
            "column_name",
            "label",
            "description",
            "physical_type",
            "value_type",
            "nullable",
        }
        specs: list[dict[str, Any]] = []
        seen_iris: set[str] = set()
        for index, item in enumerate(column_values, start=1):
            if not isinstance(item, MappingABC):
                raise DoxaBaseError(f"columns[{index}] must be an object")
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"columns[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            column_name = item.get("column_name")
            if not isinstance(column_name, str) or not column_name.strip():
                raise DoxaBaseError(
                    f"columns[{index}].column_name must be a non-empty string"
                )
            column_iri_value = item.get("column_iri", item.get("iri"))
            if column_iri_value is None:
                column_iri = self._default_table_bundle_column_iri(
                    dataset_iri,
                    column_name,
                )
            elif isinstance(column_iri_value, str):
                column_iri = str(
                    self._resource_ref(
                        f"columns[{index}].column_iri",
                        column_iri_value,
                    )
                )
            else:
                raise DoxaBaseError(
                    f"columns[{index}].column_iri must be a string when provided"
                )
            if column_iri in seen_iris:
                raise DoxaBaseError(f"columns[{index}].column_iri duplicates {column_iri}")
            seen_iris.add(column_iri)

            def optional_string(field: str) -> str | None:
                value = item.get(field)
                if value is None:
                    return None
                if not isinstance(value, str):
                    raise DoxaBaseError(f"columns[{index}].{field} must be a string")
                return value

            physical_type = optional_string("physical_type")
            value_type = optional_string("value_type")
            if physical_type is not None:
                self._resource_ref(f"columns[{index}].physical_type", physical_type)
            if value_type is not None:
                self._resource_ref(f"columns[{index}].value_type", value_type)
            nullable = item.get("nullable")
            if nullable is not None and not isinstance(nullable, bool):
                raise DoxaBaseError(f"columns[{index}].nullable must be a boolean")
            specs.append(
                {
                    "iri": column_iri,
                    "column_name": column_name.strip(),
                    "label": optional_string("label"),
                    "description": optional_string("description"),
                    "physical_type": physical_type,
                    "value_type": value_type,
                    "nullable": nullable,
                }
            )
        return specs
    @staticmethod
    def _default_table_bundle_column_iri(dataset_iri: str, column_name: str) -> str:
        local_name = re.sub(r"[^A-Za-z0-9_]+", "_", column_name.strip()).strip("_")
        if not local_name:
            raise DoxaBaseError("column_name must contain an IRI-safe character")
        return f"{dataset_iri}__{local_name}"
