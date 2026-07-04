"""Map fact recording: datasets, columns, manifests, packets.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via MapAuthoringMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class MapAuthoringMixin:
    def _analysis_caveat_severity(
        self,
        severity: ResourceSummary | None,
    ) -> str:
        if severity is None:
            return "info"
        if severity.iri in {
            self.expand_iri("rc:Moderate"),
            self.expand_iri("rc:Severe"),
        }:
            return "warning"
        return "info"
    def _upstream_caveats_for_dataset(
        self,
        direct_caveat_iris: Iterable[str],
        relationships: Iterable[RelationshipDescription],
    ) -> list[CaveatDescription]:
        direct_caveat_set = set(direct_caveat_iris)
        upstream_by_iri: dict[str, CaveatDescription] = {}
        for relationship in relationships:
            for caveat in relationship.source_caveats:
                if caveat.iri not in direct_caveat_set:
                    upstream_by_iri.setdefault(caveat.iri, caveat)
        return sorted(
            upstream_by_iri.values(),
            key=lambda caveat: (caveat.label or "", caveat.iri),
        )
    def record_map_dataset(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        is_table: bool | None = None,
        columns: Iterable[str] | str | None = None,
        path_templates: Iterable[str] | str | None = None,
        row_count_snapshot: int | None = None,
        row_semantics: str | None = None,
        entity_key: str | None = None,
        schema_stability: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        caveats: Iterable[str] | str | None = None,
        storage_accesses: Iterable[str] | str | None = None,
        physical_layouts: Iterable[str] | str | None = None,
        companion_datasets: Iterable[str] | str | None = None,
        extra_types: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        dataset_iri = self._required_iri("iri", iri)
        self._ensure_non_negative("row_count_snapshot", row_count_snapshot)
        column_values = self._string_values("columns", columns)
        path_template_values = self._string_values("path_templates", path_templates)
        caveat_values = self._string_values("caveats", caveats)
        storage_access_values = self._string_values("storage_accesses", storage_accesses)
        physical_layout_values = self._string_values("physical_layouts", physical_layouts)
        companion_values = self._string_values("companion_datasets", companion_datasets)
        extra_type_values = self._string_values("extra_types", extra_types)
        column_refs = [self._resource_ref("columns", column) for column in column_values]
        caveat_refs = [self._resource_ref("caveats", caveat) for caveat in caveat_values]
        storage_access_refs = [
            self._resource_ref("storage_accesses", access)
            for access in storage_access_values
        ]
        physical_layout_refs = [
            self._resource_ref("physical_layouts", layout)
            for layout in physical_layout_values
        ]
        companion_refs = [
            self._resource_ref("companion_datasets", companion)
            for companion in companion_values
        ]
        extra_type_refs = [
            self._resource_ref("extra_types", type_value)
            for type_value in extra_type_values
        ]
        row_semantics_ref = (
            self._controlled_resource_ref(
                "row_semantics",
                row_semantics,
                ROW_SEMANTICS_TYPES,
            )
            if row_semantics is not None
            else None
        )
        entity_key_ref = (
            self._resource_ref("entity_key", entity_key)
            if entity_key is not None
            else None
        )
        schema_stability_ref = (
            self._controlled_resource_ref(
                "schema_stability",
                schema_stability,
                SCHEMA_STABILITY_LEVELS,
            )
            if schema_stability is not None
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

        dataset_type = self.expand_iri("rc:Dataset")
        table_type = self.expand_iri("rc:Table")
        expanded_extra_types = [str(type_ref) for type_ref in extra_type_refs]
        current_types = set(self._types("map", dataset_iri))
        dataset_is_table = is_table is True or (
            is_table is None
            and (table_type in current_types or table_type in expanded_extra_types)
        )

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(dataset_iri)
        graph.add((subject, RDF.type, URIRef(dataset_type)))
        if dataset_is_table:
            graph.add((subject, RDF.type, URIRef(table_type)))
        for type_ref in extra_type_refs:
            graph.add((subject, RDF.type, type_ref))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        for column_ref in column_refs:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasColumn")),
                    column_ref,
                )
            )
        for path_template in path_template_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:pathTemplate")),
                    Literal(path_template),
                )
            )
        if row_count_snapshot is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:rowCountSnapshot")),
                    Literal(row_count_snapshot, datatype=XSD.integer),
                )
            )
        if row_semantics is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:rowSemantics")),
                    row_semantics_ref,
                )
            )
        if entity_key is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:entityKey")),
                    entity_key_ref,
                )
            )
        if schema_stability is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:schemaStability")),
                    schema_stability_ref,
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    layout_verification_status_ref,
                )
            )
        self._add_optional_literal(
            graph,
            subject,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )
        for caveat_ref in caveat_refs:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasKnownCaveat")),
                    caveat_ref,
                )
            )
        for access_ref in storage_access_refs:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasStorageAccess")),
                    access_ref,
                )
            )
        for layout_ref in physical_layout_refs:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasPhysicalLayout")),
                    layout_ref,
                )
            )
        for companion_ref in companion_refs:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:companionOf")),
                    companion_ref,
                )
            )

        predicates: list[str] = []
        if is_table is not None or not current_types:
            predicates.append(str(RDF.type))
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if columns is not None:
            predicates.append(self.expand_iri("rc:hasColumn"))
        if path_templates is not None:
            predicates.append(self.expand_iri("rc:pathTemplate"))
        if row_count_snapshot is not None:
            predicates.append(self.expand_iri("rc:rowCountSnapshot"))
        if row_semantics is not None:
            predicates.append(self.expand_iri("rc:rowSemantics"))
        if entity_key is not None:
            predicates.append(self.expand_iri("rc:entityKey"))
        if schema_stability is not None:
            predicates.append(self.expand_iri("rc:schemaStability"))
        if layout_verification_status is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationStatus"))
        if layout_verification_note is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationNote"))
        if caveats is not None:
            predicates.append(self.expand_iri("rc:hasKnownCaveat"))
        if storage_accesses is not None:
            predicates.append(self.expand_iri("rc:hasStorageAccess"))
        if physical_layouts is not None:
            predicates.append(self.expand_iri("rc:hasPhysicalLayout"))
        if companion_datasets is not None:
            predicates.append(self.expand_iri("rc:companionOf"))
        triples = self._replace_subject_triples("map", dataset_iri, predicates, graph)
        resource_type = table_type if dataset_is_table else dataset_type
        return MapResourceRecord(
            iri=dataset_iri,
            resource_type=resource_type,
            graph="map",
            triples=triples,
        )
    def record_map_table_bundle(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        columns: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        path_templates: Iterable[str] | str | None = None,
        row_count_snapshot: int | None = None,
        row_semantics: str | None = None,
        entity_key: str | None = None,
        schema_stability: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        caveats: Iterable[str] | str | None = None,
        companion_datasets: Iterable[str] | str | None = None,
        extra_types: Iterable[str] | str | None = None,
        storage_access_iri: str | None = None,
        storage_label: str | None = None,
        storage_description: str | None = None,
        route_roles: Iterable[str] | str | None = None,
        storage_protocol: str | None = None,
        access_mode: str | None = None,
        location_kind: str | None = None,
        storage_root: str | None = None,
        endpoint_profile: str | None = None,
        bucket_name: str | None = None,
        key_prefix: str | None = None,
        region: str | None = None,
        path_style_access: bool | None = None,
        credential_reference: str | None = None,
        storage_path_templates: Iterable[str] | str | None = None,
        storage_layout_verification_status: str | None = None,
        storage_layout_verification_note: str | None = None,
        physical_layout_iri: str | None = None,
        physical_layout_label: str | None = None,
        physical_layout_description: str | None = None,
        file_format: str | None = None,
        compression_codec: str | None = None,
        physical_layout_verification_status: str | None = None,
        physical_layout_verification_note: str | None = None,
    ) -> MapTableBundleRecord:
        dataset_iri = self._required_iri("iri", iri)
        columns_supplied = columns is not None
        column_specs = self._normalise_table_bundle_column_specs(
            dataset_iri,
            columns,
        )

        storage_requested = any(
            value is not None
            for value in (
                storage_access_iri,
                storage_label,
                storage_description,
                route_roles,
                storage_protocol,
                access_mode,
                location_kind,
                storage_root,
                endpoint_profile,
                bucket_name,
                key_prefix,
                region,
                path_style_access,
                credential_reference,
                storage_path_templates,
                storage_layout_verification_status,
                storage_layout_verification_note,
            )
        )
        physical_layout_requested = any(
            value is not None
            for value in (
                physical_layout_iri,
                physical_layout_label,
                physical_layout_description,
                file_format,
                compression_codec,
                physical_layout_verification_status,
                physical_layout_verification_note,
            )
        )
        storage_iri = (
            str(self._resource_ref("storage_access_iri", storage_access_iri))
            if storage_access_iri is not None
            else f"{dataset_iri}/storage-access/1"
        )
        physical_layout_value = (
            str(self._resource_ref("physical_layout_iri", physical_layout_iri))
            if physical_layout_iri is not None
            else f"{dataset_iri}/physical-layout/1"
        )

        self._preflight_map_table_bundle(
            label=label,
            description=description,
            path_templates=path_templates,
            row_count_snapshot=row_count_snapshot,
            row_semantics=row_semantics,
            entity_key=entity_key,
            schema_stability=schema_stability,
            layout_verification_status=layout_verification_status,
            layout_verification_note=layout_verification_note,
            caveats=caveats,
            companion_datasets=companion_datasets,
            extra_types=extra_types,
            storage_label=storage_label,
            storage_description=storage_description,
            route_roles=route_roles,
            storage_protocol=storage_protocol,
            access_mode=access_mode,
            location_kind=location_kind,
            storage_root=storage_root,
            endpoint_profile=endpoint_profile,
            bucket_name=bucket_name,
            key_prefix=key_prefix,
            region=region,
            path_style_access=path_style_access,
            credential_reference=credential_reference,
            storage_path_templates=storage_path_templates,
            storage_layout_verification_status=storage_layout_verification_status,
            storage_layout_verification_note=storage_layout_verification_note,
            physical_layout_label=physical_layout_label,
            physical_layout_description=physical_layout_description,
            file_format=file_format,
            compression_codec=compression_codec,
            physical_layout_verification_status=physical_layout_verification_status,
            physical_layout_verification_note=physical_layout_verification_note,
        )

        storage_record = (
            self.record_map_storage_access(
                storage_iri,
                label=storage_label,
                description=storage_description,
                route_roles=route_roles,
                storage_protocol=storage_protocol,
                access_mode=access_mode,
                location_kind=location_kind,
                storage_root=storage_root,
                endpoint_profile=endpoint_profile,
                bucket_name=bucket_name,
                key_prefix=key_prefix,
                region=region,
                path_style_access=path_style_access,
                credential_reference=credential_reference,
                path_templates=storage_path_templates,
                layout_verification_status=storage_layout_verification_status,
                layout_verification_note=storage_layout_verification_note,
                datasets=[dataset_iri],
            )
            if storage_requested
            else None
        )
        physical_layout_record = (
            self.record_map_physical_layout(
                physical_layout_value,
                label=physical_layout_label,
                description=physical_layout_description,
                file_format=file_format,
                compression_codec=compression_codec,
                layout_verification_status=physical_layout_verification_status,
                layout_verification_note=physical_layout_verification_note,
                datasets=[dataset_iri],
            )
            if physical_layout_requested
            else None
        )

        dataset_record = self.record_map_dataset(
            dataset_iri,
            label=label,
            description=description,
            is_table=True,
            columns=[spec["iri"] for spec in column_specs] if columns_supplied else None,
            path_templates=path_templates,
            row_count_snapshot=row_count_snapshot,
            row_semantics=row_semantics,
            entity_key=entity_key,
            schema_stability=schema_stability,
            layout_verification_status=layout_verification_status,
            layout_verification_note=layout_verification_note,
            caveats=caveats,
            storage_accesses=[storage_iri] if storage_requested else None,
            physical_layouts=(
                [physical_layout_value] if physical_layout_requested else None
            ),
            companion_datasets=companion_datasets,
            extra_types=extra_types,
        )
        column_records = [
            self.record_map_column(
                spec["iri"],
                table_iri=dataset_iri,
                column_name=spec["column_name"],
                label=spec["label"],
                description=spec["description"],
                physical_type=spec["physical_type"],
                value_type=spec["value_type"],
                nullable=spec["nullable"],
            )
            for spec in column_specs
        ]
        suggested_next_actions = [
            SuggestedNextAction(
                tool="doxabase.describe_dataset",
                args={"iri": dataset_iri},
                reason="Inspect the map table bundle just recorded, including "
                    "columns, storage access, and physical layout links.",
            ),
            SuggestedNextAction(
                tool="doxabase.describe_query_context",
                args={"iri": dataset_iri},
                reason="Check whether the bundled table metadata is sufficient for "
                    "query planning or needs reviewed storage/layout repairs.",
            ),
        ]
        return MapTableBundleRecord(
            dataset=dataset_record,
            storage_access=storage_record,
            physical_layout=physical_layout_record,
            columns=column_records,
            column_iris=[record.iri for record in column_records],
            suggested_next_actions=suggested_next_actions,
        )
    def record_map_column(
        self,
        iri: str,
        *,
        column_name: str,
        table_iri: str | None = None,
        label: str | None = None,
        description: str | None = None,
        physical_type: str | None = None,
        value_type: str | None = None,
        nullable: bool | None = None,
    ) -> MapResourceRecord:
        column_iri = self._required_iri("iri", iri)
        column_name_value = column_name.strip()
        if not column_name_value:
            raise DoxaBaseError("column_name must not be empty")
        physical_type_ref = (
            self._resource_ref("physical_type", physical_type)
            if physical_type is not None
            else None
        )
        value_type_ref = (
            self._resource_ref("value_type", value_type)
            if value_type is not None
            else None
        )
        table_ref = (
            self._resource_ref("table_iri", table_iri)
            if table_iri is not None
            else None
        )

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(column_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:Column"))))
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:columnName")),
                Literal(column_name_value),
            )
        )
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        if physical_type is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:physicalType")),
                    physical_type_ref,
                )
            )
        if value_type is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:valueType")),
                    value_type_ref,
                )
            )
        if nullable is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:nullable")),
                    Literal(nullable, datatype=XSD.boolean),
                )
            )

        predicates = [
            str(RDF.type),
            self.expand_iri("rc:columnName"),
        ]
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if physical_type is not None:
            predicates.append(self.expand_iri("rc:physicalType"))
        if value_type is not None:
            predicates.append(self.expand_iri("rc:valueType"))
        if nullable is not None:
            predicates.append(self.expand_iri("rc:nullable"))
        triples = self._replace_subject_triples("map", column_iri, predicates, graph)
        if table_iri is not None:
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            link_graph.add(
                (
                    table_ref,
                    URIRef(self.expand_iri("rc:hasColumn")),
                    subject,
                )
            )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=column_iri,
            resource_type=self.expand_iri("rc:Column"),
            graph="map",
            triples=triples,
        )
    def record_map_caveat(
        self,
        iri: str,
        *,
        description: str,
        label: str | None = None,
        impact: str | None = None,
        severity: str | None = None,
        targets: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        caveat_iri = self._required_iri("iri", iri)
        description_value = description.strip()
        if not description_value:
            raise DoxaBaseError("description must not be empty")
        target_values = self._string_values("targets", targets)
        severity_ref = (
            self._controlled_resource_ref(
                "severity",
                severity,
                CAVEAT_SEVERITY_LEVELS,
            )
            if severity is not None
            else None
        )

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(caveat_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:KnownCaveat"))))
        graph.add(
            (
                subject,
                URIRef(self.expand_iri("rc:caveatDescription")),
                Literal(description_value),
            )
        )
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, "rc:impact", impact)
        if severity is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:severity")),
                    severity_ref,
                )
            )

        predicates = [
            str(RDF.type),
            self.expand_iri("rc:caveatDescription"),
        ]
        if label is not None:
            predicates.append(str(RDFS.label))
        if impact is not None:
            predicates.append(self.expand_iri("rc:impact"))
        if severity is not None:
            predicates.append(self.expand_iri("rc:severity"))
        triples = self._replace_subject_triples("map", caveat_iri, predicates, graph)
        if target_values:
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            for target in target_values:
                link_graph.add(
                    (
                        self._resource_ref("targets", target),
                        URIRef(self.expand_iri("rc:hasKnownCaveat")),
                        subject,
                    )
                )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=caveat_iri,
            resource_type=self.expand_iri("rc:KnownCaveat"),
            graph="map",
            triples=triples,
        )
    def record_map_storage_access(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        route_roles: Iterable[str] | str | None = None,
        storage_protocol: str | None = None,
        access_mode: str | None = None,
        location_kind: str | None = None,
        storage_root: str | None = None,
        endpoint_profile: str | None = None,
        bucket_name: str | None = None,
        key_prefix: str | None = None,
        region: str | None = None,
        path_style_access: bool | None = None,
        credential_reference: str | None = None,
        path_templates: Iterable[str] | str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        datasets: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        access_iri = self._required_iri("iri", iri)
        route_role_values = self._string_values("route_roles", route_roles)
        path_template_values = self._string_values("path_templates", path_templates)
        dataset_values = self._string_values("datasets", datasets)
        location_kind_value = self._storage_location_kind(location_kind)
        storage_protocol_ref = (
            self._resource_ref("storage_protocol", storage_protocol)
            if storage_protocol is not None
            else None
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

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(access_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:StorageAccess"))))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        for route_role in route_role_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:routeRole")),
                    self._resource_ref("route_roles", route_role),
                )
            )
        if storage_protocol is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:storageProtocol")),
                    storage_protocol_ref,
                )
            )
        if access_mode is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:accessMode")),
                    access_mode_ref,
                )
            )
        for predicate, value in (
            ("rc:locationKind", location_kind_value),
            ("rc:storageRoot", storage_root),
            ("rc:endpointProfile", endpoint_profile),
            ("rc:bucketName", bucket_name),
            ("rc:keyPrefix", key_prefix),
            ("rc:region", region),
            ("rc:credentialReference", credential_reference),
        ):
            self._add_optional_literal(graph, subject, predicate, value)
        if path_style_access is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:pathStyleAccess")),
                    Literal(path_style_access, datatype=XSD.boolean),
                )
            )
        for path_template in path_template_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:pathTemplate")),
                    Literal(path_template),
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    layout_verification_status_ref,
                )
            )
        self._add_optional_literal(
            graph,
            subject,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )

        predicates = [str(RDF.type)]
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if route_roles is not None:
            predicates.append(self.expand_iri("rc:routeRole"))
        if storage_protocol is not None:
            predicates.append(self.expand_iri("rc:storageProtocol"))
        if access_mode is not None:
            predicates.append(self.expand_iri("rc:accessMode"))
        if location_kind is not None:
            predicates.append(self.expand_iri("rc:locationKind"))
        if storage_root is not None:
            predicates.append(self.expand_iri("rc:storageRoot"))
        if endpoint_profile is not None:
            predicates.append(self.expand_iri("rc:endpointProfile"))
        if bucket_name is not None:
            predicates.append(self.expand_iri("rc:bucketName"))
        if key_prefix is not None:
            predicates.append(self.expand_iri("rc:keyPrefix"))
        if region is not None:
            predicates.append(self.expand_iri("rc:region"))
        if credential_reference is not None:
            predicates.append(self.expand_iri("rc:credentialReference"))
        if path_style_access is not None:
            predicates.append(self.expand_iri("rc:pathStyleAccess"))
        if path_templates is not None:
            predicates.append(self.expand_iri("rc:pathTemplate"))
        if layout_verification_status is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationStatus"))
        if layout_verification_note is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationNote"))
        triples = self._replace_subject_triples("map", access_iri, predicates, graph)
        if dataset_values:
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            for dataset in dataset_values:
                link_graph.add(
                    (
                        self._resource_ref("datasets", dataset),
                        URIRef(self.expand_iri("rc:hasStorageAccess")),
                        subject,
                    )
                )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=access_iri,
            resource_type=self.expand_iri("rc:StorageAccess"),
            graph="map",
            triples=triples,
        )
    def record_map_physical_layout(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        file_format: str | None = None,
        compression_codec: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        datasets: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        layout_iri = self._required_iri("iri", iri)
        dataset_values = self._string_values("datasets", datasets)
        file_format_ref = (
            self._resource_ref("file_format", file_format)
            if file_format is not None
            else None
        )
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

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(layout_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:PhysicalLayout"))))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        if file_format is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:fileFormat")),
                    file_format_ref,
                )
            )
        if compression_codec is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:compressionCodec")),
                    compression_codec_ref,
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    layout_verification_status_ref,
                )
            )
        self._add_optional_literal(
            graph,
            subject,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )

        predicates = [str(RDF.type)]
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if file_format is not None:
            predicates.append(self.expand_iri("rc:fileFormat"))
        if compression_codec is not None:
            predicates.append(self.expand_iri("rc:compressionCodec"))
        if layout_verification_status is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationStatus"))
        if layout_verification_note is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationNote"))
        triples = self._replace_subject_triples("map", layout_iri, predicates, graph)
        if dataset_values:
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            for dataset in dataset_values:
                link_graph.add(
                    (
                        self._resource_ref("datasets", dataset),
                        URIRef(self.expand_iri("rc:hasPhysicalLayout")),
                        subject,
                    )
                )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=layout_iri,
            resource_type=self.expand_iri("rc:PhysicalLayout"),
            graph="map",
            triples=triples,
        )
    def record_map_partition_scheme(
        self,
        iri: str,
        *,
        label: str | None = None,
        description: str | None = None,
        partition_columns: Iterable[str] | str | None = None,
        granularity: str | None = None,
        path_template: str | None = None,
        redundant_partition_key: str | None = None,
        layout_verification_status: str | None = None,
        layout_verification_note: str | None = None,
        datasets: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        partition_iri = self._required_iri("iri", iri)
        partition_column_values = self._string_values(
            "partition_columns",
            partition_columns,
        )
        dataset_values = self._string_values("datasets", datasets)
        granularity_ref = (
            self._controlled_resource_ref(
                "granularity",
                granularity,
                PARTITION_GRANULARITIES,
            )
            if granularity is not None
            else None
        )
        redundant_partition_key_ref = (
            self._resource_ref("redundant_partition_key", redundant_partition_key)
            if redundant_partition_key is not None
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

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(partition_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri("rc:PartitionScheme"))))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        for partition_column in partition_column_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:partitionColumn")),
                    self._resource_ref("partition_columns", partition_column),
                )
            )
        if granularity is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:partitionGranularity")),
                    granularity_ref,
                )
            )
        self._add_optional_literal(graph, subject, "rc:pathTemplate", path_template)
        if redundant_partition_key is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:redundantPartitionKey")),
                    redundant_partition_key_ref,
                )
            )
        if layout_verification_status is not None:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:layoutVerificationStatus")),
                    layout_verification_status_ref,
                )
            )
        self._add_optional_literal(
            graph,
            subject,
            "rc:layoutVerificationNote",
            layout_verification_note,
        )

        predicates = [str(RDF.type)]
        if label is not None:
            predicates.append(str(RDFS.label))
        if description is not None:
            predicates.append(str(RDFS.comment))
        if partition_columns is not None:
            predicates.append(self.expand_iri("rc:partitionColumn"))
        if granularity is not None:
            predicates.append(self.expand_iri("rc:partitionGranularity"))
        if path_template is not None:
            predicates.append(self.expand_iri("rc:pathTemplate"))
        if redundant_partition_key is not None:
            predicates.append(self.expand_iri("rc:redundantPartitionKey"))
        if layout_verification_status is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationStatus"))
        if layout_verification_note is not None:
            predicates.append(self.expand_iri("rc:layoutVerificationNote"))
        triples = self._replace_subject_triples("map", partition_iri, predicates, graph)
        if dataset_values:
            link_graph = Graph()
            self._bind_prefixes(link_graph)
            for dataset in dataset_values:
                link_graph.add(
                    (
                        self._resource_ref("datasets", dataset),
                        URIRef(self.expand_iri("rc:partitionedBy")),
                        subject,
                    )
                )
            triples += self._insert_graph("map", link_graph)
        return MapResourceRecord(
            iri=partition_iri,
            resource_type=self.expand_iri("rc:PartitionScheme"),
            graph="map",
            triples=triples,
        )
    def record_map_relationship(
        self,
        iri: str,
        *,
        relationship_type: str,
        label: str | None = None,
        description: str | None = None,
        source_dataset: str | None = None,
        target_dataset: str | None = None,
        source_datasets: Iterable[str] | str | None = None,
        target_datasets: Iterable[str] | str | None = None,
        source_endpoints: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        target_endpoints: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        from_column: str | None = None,
        to_column: str | None = None,
        identifying_columns: Iterable[str] | str | None = None,
        source_columns: Iterable[str] | str | None = None,
        derived_columns: Iterable[str] | str | None = None,
        group_by_columns: Iterable[str] | str | None = None,
        aggregated_columns: (
            Iterable[Mapping[str, Any]] | Mapping[str, Any] | None
        ) = None,
        declared: bool | None = None,
        referential_integrity: str | None = None,
        derivation_function: str | None = None,
        derivation_properties: Iterable[str] | str | None = None,
    ) -> MapResourceRecord:
        relationship_iri = self._required_iri("iri", iri)
        relationship_type = self._normalise_relationship_type(relationship_type)
        identifying_column_values = self._string_values(
            "identifying_columns",
            identifying_columns,
        )
        source_column_values = self._string_values("source_columns", source_columns)
        derived_column_values = self._string_values("derived_columns", derived_columns)
        group_by_column_values = self._string_values(
            "group_by_columns",
            group_by_columns,
        )
        source_dataset_values = self._relationship_endpoint_values(
            "source_datasets",
            source_dataset,
            source_datasets,
        )
        target_dataset_values = self._relationship_endpoint_values(
            "target_datasets",
            target_dataset,
            target_datasets,
        )
        source_endpoint_specs = self._normalise_relationship_endpoint_specs(
            "source_endpoints",
            source_endpoints,
            relationship_iri=relationship_iri,
            direction="source",
        )
        target_endpoint_specs = self._normalise_relationship_endpoint_specs(
            "target_endpoints",
            target_endpoints,
            relationship_iri=relationship_iri,
            direction="target",
        )
        source_dataset_values = list(
            dict.fromkeys(
                [
                    *source_dataset_values,
                    *(spec["dataset"] for spec in source_endpoint_specs),
                ]
            )
        )
        target_dataset_values = list(
            dict.fromkeys(
                [
                    *target_dataset_values,
                    *(spec["dataset"] for spec in target_endpoint_specs),
                ]
            )
        )
        aggregated_column_values = self._normalise_aggregated_column_specs(
            aggregated_columns,
        )
        derivation_property_values = self._string_values(
            "derivation_properties",
            derivation_properties,
        )
        derivation_property_refs = [
            self._controlled_resource_ref(
                "derivation_properties",
                value,
                DERIVATION_PROPERTIES,
            )
            for value in derivation_property_values
        ]
        resource_type = RELATIONSHIP_TYPE_IRIS[relationship_type]
        if relationship_type == "foreign_key" and (from_column is None or to_column is None):
            raise DoxaBaseError(
                "foreign_key relationships require from_column and to_column"
            )
        if relationship_type == "shared_identifier" and len(identifying_column_values) < 2:
            raise DoxaBaseError(
                "shared_identifier relationships require at least two identifying_columns"
            )
        endpoint_pair_present = bool(source_dataset_values and target_dataset_values)
        if relationship_type == "derivation" and (
            (not source_column_values or not derived_column_values)
            and not endpoint_pair_present
        ):
            raise DoxaBaseError(
                "derivation relationships require source_columns and "
                "derived_columns, or source_datasets and target_datasets for "
                "asset-level derivations"
            )
        if (
            relationship_type == "aggregation"
            and not aggregated_column_values
            and not endpoint_pair_present
        ):
            raise DoxaBaseError(
                "aggregation relationships require at least one "
                "aggregated_columns entry, or source_datasets and "
                "target_datasets for asset-level aggregations"
            )
        self._validate_relationship_column_resources(
            from_column=from_column,
            to_column=to_column,
            identifying_columns=identifying_column_values,
            source_columns=source_column_values,
            derived_columns=derived_column_values,
            group_by_columns=group_by_column_values,
            aggregated_columns=aggregated_column_values,
        )
        self._validate_dataset_endpoint_resources(
            [
                *(
                    (endpoint_spec["field"], endpoint_spec["dataset"])
                    for endpoint_spec in [
                        *source_endpoint_specs,
                        *target_endpoint_specs,
                    ]
                ),
                *(("source_datasets", value) for value in source_dataset_values),
                *(("target_datasets", value) for value in target_dataset_values),
            ]
        )

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(relationship_iri)
        graph.add((subject, RDF.type, URIRef(self.expand_iri(resource_type))))
        self._add_optional_literal(graph, subject, str(RDFS.label), label)
        self._add_optional_literal(graph, subject, str(RDFS.comment), description)
        for source_dataset_value in source_dataset_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:sourceDataset")),
                    self._resource_ref("source_datasets", source_dataset_value),
                )
            )
        for target_dataset_value in target_dataset_values:
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:targetDataset")),
                    self._resource_ref("target_datasets", target_dataset_value),
                )
            )
        for endpoint_spec in [*source_endpoint_specs, *target_endpoint_specs]:
            endpoint = URIRef(endpoint_spec["iri"])
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasRelationshipEndpoint")),
                    endpoint,
                )
            )
            graph.add(
                (
                    endpoint,
                    RDF.type,
                    URIRef(self.expand_iri("rc:RelationshipEndpoint")),
                )
            )
            graph.add(
                (
                    endpoint,
                    URIRef(self.expand_iri("rc:endpointDataset")),
                    self._resource_ref(endpoint_spec["field"], endpoint_spec["dataset"]),
                )
            )
            graph.add(
                (
                    endpoint,
                    URIRef(self.expand_iri("rc:endpointDirection")),
                    URIRef(
                        self.expand_iri(
                            "rc:SourceEndpoint"
                            if endpoint_spec["direction"] == "source"
                            else "rc:TargetEndpoint"
                        )
                    ),
                )
            )
            graph.add(
                (
                    endpoint,
                    URIRef(self.expand_iri("rc:endpointOrder")),
                    Literal(endpoint_spec["order"], datatype=XSD.integer),
                )
            )
            if endpoint_spec["role"] is not None:
                graph.add(
                    (
                        endpoint,
                        URIRef(self.expand_iri("rc:endpointRole")),
                        Literal(endpoint_spec["role"]),
                    )
                )
        if relationship_type == "foreign_key":
            assert from_column is not None
            assert to_column is not None
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:foreignKeyFrom")),
                    self._resource_ref("from_column", from_column),
                )
            )
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:foreignKeyTo")),
                    self._resource_ref("to_column", to_column),
                )
            )
            if declared is not None:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:declared")),
                        Literal(declared, datatype=XSD.boolean),
                    )
                )
            if referential_integrity is not None:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:referentialIntegrity")),
                        self._resource_ref(
                            "referential_integrity",
                            referential_integrity,
                        ),
                    )
                )
        if relationship_type == "shared_identifier":
            for column in identifying_column_values:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:identifyingColumn")),
                        self._resource_ref("identifying_columns", column),
                    )
                )
        if relationship_type == "derivation":
            for column in source_column_values:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:sourceColumn")),
                        self._resource_ref("source_columns", column),
                    )
                )
            for column in derived_column_values:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:derivedColumn")),
                        self._resource_ref("derived_columns", column),
                    )
                )
            if derivation_function is not None:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:derivationFunction")),
                        self._resource_ref(
                            "derivation_function",
                            derivation_function,
                        ),
                    )
                )
            for derivation_property_ref in derivation_property_refs:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:hasDerivationProperty")),
                        derivation_property_ref,
                    )
                )

        if relationship_type == "aggregation":
            for column in group_by_column_values:
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:groupByColumn")),
                        self._resource_ref("group_by_columns", column),
                    )
                )
            for index, aggregated_column in enumerate(aggregated_column_values, start=1):
                mapping_subject = (
                    self._resource_ref(
                        f"aggregated_columns[{index}].iri",
                        aggregated_column["iri"],
                    )
                    if aggregated_column["iri"] is not None
                    else URIRef(f"{relationship_iri}/aggregated-column/{index}")
                )
                graph.add(
                    (
                        subject,
                        URIRef(self.expand_iri("rc:hasAggregatedColumn")),
                        mapping_subject,
                    )
                )
                graph.add(
                    (
                        mapping_subject,
                        RDF.type,
                        URIRef(self.expand_iri("rc:AggregatedColumn")),
                    )
                )
                graph.add(
                    (
                        mapping_subject,
                        URIRef(self.expand_iri("rc:targetColumn")),
                        self._resource_ref(
                            f"aggregated_columns[{index}].target_column",
                            aggregated_column["target_column"],
                        ),
                    )
                )
                for column in aggregated_column["source_columns"]:
                    graph.add(
                        (
                            mapping_subject,
                            URIRef(self.expand_iri("rc:aggregationSourceColumn")),
                            self._resource_ref(
                                f"aggregated_columns[{index}].source_columns",
                                column,
                            ),
                        )
                    )
                if aggregated_column["aggregation_function"] is not None:
                    graph.add(
                        (
                            mapping_subject,
                            URIRef(self.expand_iri("rc:aggregationFunction")),
                            self._resource_ref(
                                f"aggregated_columns[{index}].aggregation_function",
                                aggregated_column["aggregation_function"],
                            ),
                        )
                    )
                if aggregated_column["within_group_ordering"] is not None:
                    graph.add(
                        (
                            mapping_subject,
                            URIRef(self.expand_iri("rc:withinGroupOrdering")),
                            self._resource_ref(
                                f"aggregated_columns[{index}].within_group_ordering",
                                aggregated_column["within_group_ordering"],
                            ),
                        )
                    )

        predicates = [
            str(RDF.type),
            str(RDFS.label),
            str(RDFS.comment),
            self.expand_iri("rc:sourceDataset"),
            self.expand_iri("rc:targetDataset"),
            self.expand_iri("rc:hasRelationshipEndpoint"),
            self.expand_iri("rc:foreignKeyFrom"),
            self.expand_iri("rc:foreignKeyTo"),
            self.expand_iri("rc:declared"),
            self.expand_iri("rc:referentialIntegrity"),
            self.expand_iri("rc:identifyingColumn"),
            self.expand_iri("rc:sourceColumn"),
            self.expand_iri("rc:derivedColumn"),
            self.expand_iri("rc:derivationFunction"),
            self.expand_iri("rc:hasDerivationProperty"),
            self.expand_iri("rc:groupByColumn"),
            self.expand_iri("rc:hasAggregatedColumn"),
        ]
        self._delete_existing_relationship_endpoint_triples(relationship_iri)
        self._delete_existing_aggregated_column_triples(relationship_iri)
        triples = self._replace_subject_triples(
            "map",
            relationship_iri,
            predicates,
            graph,
        )
        return MapResourceRecord(
            iri=relationship_iri,
            resource_type=self.expand_iri(resource_type),
            graph="map",
            triples=triples,
        )
    def record_map_asset_transform(
        self,
        iri: str,
        *,
        relationship_type: str,
        label: str | None = None,
        description: str | None = None,
        source_dataset: str | None = None,
        target_dataset: str | None = None,
        source_datasets: Iterable[str] | str | None = None,
        target_datasets: Iterable[str] | str | None = None,
        source_endpoints: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        target_endpoints: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        derivation_properties: Iterable[str] | str | None = None,
        conditions: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        outputs: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    ) -> MapResourceRecord:
        relationship_type = self._normalise_relationship_type(
            relationship_type,
            allowed_tokens=("derivation", "aggregation"),
            context="asset transform relationship_type",
        )
        relationship_iri = self._required_iri("iri", iri)
        condition_specs = self._normalise_transform_condition_specs(
            conditions,
            relationship_iri=relationship_iri,
        )
        output_specs = self._normalise_transform_output_specs(
            outputs,
            relationship_iri=relationship_iri,
        )
        self._validate_transform_output_condition_refs(condition_specs, output_specs)
        relationship_record = self.record_map_relationship(
            relationship_iri,
            relationship_type=relationship_type,
            label=label,
            description=description,
            source_dataset=source_dataset,
            target_dataset=target_dataset,
            source_datasets=source_datasets,
            target_datasets=target_datasets,
            source_endpoints=source_endpoints,
            target_endpoints=target_endpoints,
            derivation_properties=derivation_properties,
        )

        graph = Graph()
        self._bind_prefixes(graph)
        subject = URIRef(relationship_iri)
        for condition in condition_specs:
            condition_ref = URIRef(condition["iri"])
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasTransformCondition")),
                    condition_ref,
                )
            )
            graph.add(
                (
                    condition_ref,
                    RDF.type,
                    URIRef(self.expand_iri("rc:TransformCondition")),
                )
            )
            self._add_optional_literal(
                graph,
                condition_ref,
                str(RDFS.label),
                condition["label"],
            )
            self._add_optional_literal(
                graph,
                condition_ref,
                str(RDFS.comment),
                condition["description"],
            )
            if condition["condition_kind"] is not None:
                graph.add(
                    (
                        condition_ref,
                        URIRef(self.expand_iri("rc:conditionKind")),
                        URIRef(condition["condition_kind"]),
                    )
                )
            graph.add(
                (
                    condition_ref,
                    URIRef(self.expand_iri("rc:expressionText")),
                    Literal(condition["expression"]),
                )
            )
            self._add_optional_literal(
                graph,
                condition_ref,
                "rc:expressionLanguage",
                condition["expression_language"],
            )
            for dataset in condition["applies_to_datasets"]:
                graph.add(
                    (
                        condition_ref,
                        URIRef(self.expand_iri("rc:appliesToDataset")),
                        self._resource_ref(
                            "conditions.applies_to_datasets",
                            dataset,
                        ),
                    )
                )
            for endpoint in condition["applies_to_endpoints"]:
                graph.add(
                    (
                        condition_ref,
                        URIRef(self.expand_iri("rc:appliesToEndpoint")),
                        self._resource_ref(
                            "conditions.applies_to_endpoints",
                            endpoint,
                        ),
                    )
                )

        for output in output_specs:
            output_ref = URIRef(output["iri"])
            target_dataset_ref = self._resource_ref(
                "outputs.target_dataset",
                output["target_dataset"],
            )
            graph.add(
                (
                    subject,
                    URIRef(self.expand_iri("rc:hasTransformOutput")),
                    output_ref,
                )
            )
            graph.add(
                (
                    output_ref,
                    RDF.type,
                    URIRef(self.expand_iri("rc:TransformOutput")),
                )
            )
            self._add_optional_literal(graph, output_ref, str(RDFS.label), output["label"])
            self._add_optional_literal(
                graph,
                output_ref,
                str(RDFS.comment),
                output["description"],
            )
            graph.add(
                (
                    output_ref,
                    URIRef(self.expand_iri("rc:outputDataset")),
                    target_dataset_ref,
                )
            )
            self._add_optional_literal(
                graph,
                output_ref,
                "rc:outputRole",
                output["role"],
            )
            self._add_optional_literal(
                graph,
                output_ref,
                "rc:outputFormula",
                output["formula"],
            )
            self._add_optional_literal(
                graph,
                output_ref,
                "rc:expressionLanguage",
                output["expression_language"],
            )
            if output["function"] is not None:
                graph.add(
                    (
                        output_ref,
                        URIRef(self.expand_iri("rc:outputFunction")),
                        self._resource_ref("outputs.function", output["function"]),
                    )
                )
            for condition in output["conditions"]:
                graph.add(
                    (
                        output_ref,
                        URIRef(self.expand_iri("rc:outputCondition")),
                        self._resource_ref("outputs.conditions", condition),
                    )
                )
            tuple_grain = output["tuple_grain"]
            if tuple_grain is not None:
                grain_ref = URIRef(tuple_grain["iri"])
                graph.add(
                    (
                        output_ref,
                        URIRef(self.expand_iri("rc:outputGrain")),
                        grain_ref,
                    )
                )
                graph.add(
                    (
                        target_dataset_ref,
                        URIRef(self.expand_iri("rc:hasGrain")),
                        grain_ref,
                    )
                )
                graph.add(
                    (
                        grain_ref,
                        RDF.type,
                        URIRef(self.expand_iri("rc:TupleGrain")),
                    )
                )
                self._add_optional_literal(
                    graph,
                    grain_ref,
                    str(RDFS.label),
                    tuple_grain["label"],
                )
                self._add_optional_literal(
                    graph,
                    grain_ref,
                    str(RDFS.comment),
                    tuple_grain["description"],
                )
                for component in tuple_grain["components"]:
                    component_ref = URIRef(component["iri"])
                    graph.add(
                        (
                            grain_ref,
                            URIRef(self.expand_iri("rc:hasGrainComponent")),
                            component_ref,
                        )
                    )
                    graph.add(
                        (
                            component_ref,
                            RDF.type,
                            URIRef(self.expand_iri("rc:GrainComponent")),
                        )
                    )
                    self._add_optional_literal(
                        graph,
                        component_ref,
                        str(RDFS.label),
                        component["label"],
                    )
                    self._add_optional_literal(
                        graph,
                        component_ref,
                        str(RDFS.comment),
                        component["description"],
                    )
                    graph.add(
                        (
                            component_ref,
                            URIRef(self.expand_iri("rc:grainOrder")),
                            Literal(component["order"], datatype=XSD.integer),
                        )
                    )
                    self._add_optional_literal(
                        graph,
                        component_ref,
                        "rc:grainRole",
                        component["role"],
                    )
                    if component["column"] is not None:
                        graph.add(
                            (
                                component_ref,
                                URIRef(self.expand_iri("rc:grainColumn")),
                                self._resource_ref(
                                    "tuple_grain.components.column",
                                    component["column"],
                                ),
                            )
                        )
                    if component["dataset"] is not None:
                        graph.add(
                            (
                                component_ref,
                                URIRef(self.expand_iri("rc:grainDataset")),
                                self._resource_ref(
                                    "tuple_grain.components.dataset",
                                    component["dataset"],
                                ),
                            )
                        )
                    self._add_optional_literal(
                        graph,
                        component_ref,
                        "rc:grainExpression",
                        component["expression"],
                    )

        self._delete_existing_asset_transform_triples(relationship_iri)
        transform_triples = self._insert_graph("map", graph)
        return MapResourceRecord(
            iri=relationship_iri,
            resource_type=relationship_record.resource_type,
            graph="map",
            triples=relationship_record.triples + transform_triples,
        )
    def _normalise_transform_condition_specs(
        self,
        values: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        *,
        relationship_iri: str,
    ) -> list[dict[str, Any]]:
        raw_values = self._mapping_list("conditions", values)
        specs: list[dict[str, Any]] = []
        for index, item in enumerate(raw_values, start=1):
            item_name = f"conditions[{index}]"
            expression = self._mapping_string(
                item_name,
                item,
                "expression",
                "expression_text",
                "expressionText",
                required=True,
            )
            assert expression is not None
            condition_kind = self._mapping_string(
                item_name,
                item,
                "condition_kind",
                "conditionKind",
                "kind",
            )
            condition_kind_iri = (
                str(
                    self._controlled_resource_ref(
                        f"{item_name}.condition_kind",
                        condition_kind,
                        TRANSFORM_CONDITION_KINDS,
                    )
                )
                if condition_kind is not None
                else None
            )
            condition_iri = self._mapping_string(item_name, item, "iri", "id")
            applies_to_datasets = self._string_values(
                f"{item_name}.applies_to_datasets",
                self._mapping_value(
                    item,
                    "applies_to_datasets",
                    "appliesToDatasets",
                    "applies_to_dataset",
                    "appliesToDataset",
                    "datasets",
                ),
            )
            applies_to_endpoints = self._string_values(
                f"{item_name}.applies_to_endpoints",
                self._mapping_value(
                    item,
                    "applies_to_endpoints",
                    "appliesToEndpoints",
                    "applies_to_endpoint",
                    "appliesToEndpoint",
                    "endpoints",
                ),
            )
            self._validate_resource_values(
                f"{item_name}.applies_to_datasets",
                applies_to_datasets,
            )
            self._validate_dataset_endpoint_resources(
                (
                    (f"{item_name}.applies_to_datasets", value)
                    for value in applies_to_datasets
                )
            )
            self._validate_resource_values(
                f"{item_name}.applies_to_endpoints",
                applies_to_endpoints,
            )
            specs.append(
                {
                    "iri": (
                        self._required_iri(f"{item_name}.iri", condition_iri)
                        if condition_iri is not None
                        else f"{relationship_iri}/condition/{index}"
                    ),
                    "label": self._mapping_string(item_name, item, "label"),
                    "description": self._mapping_string(
                        item_name,
                        item,
                        "description",
                        "comment",
                    ),
                    "condition_kind": condition_kind_iri,
                    "expression": expression,
                    "expression_language": self._mapping_string(
                        item_name,
                        item,
                        "expression_language",
                        "expressionLanguage",
                        "language",
                    ),
                    "applies_to_datasets": applies_to_datasets,
                    "applies_to_endpoints": applies_to_endpoints,
                }
            )
        return specs
    def _normalise_transform_output_specs(
        self,
        values: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        *,
        relationship_iri: str,
    ) -> list[dict[str, Any]]:
        raw_values = self._mapping_list("outputs", values)
        specs: list[dict[str, Any]] = []
        for index, item in enumerate(raw_values, start=1):
            item_name = f"outputs[{index}]"
            target_dataset = self._mapping_string(
                item_name,
                item,
                "target_dataset",
                "targetDataset",
                "output_dataset",
                "outputDataset",
                "dataset",
                required=True,
            )
            assert target_dataset is not None
            output_iri = self._mapping_string(item_name, item, "iri", "id")
            output_iri_value = (
                self._required_iri(f"{item_name}.iri", output_iri)
                if output_iri is not None
                else f"{relationship_iri}/output/{index}"
            )
            function = self._mapping_string(
                item_name,
                item,
                "function",
                "output_function",
                "outputFunction",
            )
            condition_values = self._string_values(
                f"{item_name}.conditions",
                self._mapping_value(
                    item,
                    "conditions",
                    "condition_iris",
                    "conditionIris",
                    "condition_iri",
                    "conditionIri",
                    "condition",
                ),
            )
            self._resource_ref(f"{item_name}.target_dataset", target_dataset)
            self._validate_dataset_endpoint_resource(
                f"{item_name}.target_dataset",
                target_dataset,
            )
            if function is not None:
                self._resource_ref(f"{item_name}.function", function)
            self._validate_resource_values(f"{item_name}.conditions", condition_values)
            specs.append(
                {
                    "iri": output_iri_value,
                    "label": self._mapping_string(item_name, item, "label"),
                    "description": self._mapping_string(
                        item_name,
                        item,
                        "description",
                        "comment",
                    ),
                    "target_dataset": target_dataset,
                    "role": self._mapping_string(
                        item_name,
                        item,
                        "role",
                        "output_role",
                        "outputRole",
                    ),
                    "formula": self._mapping_string(
                        item_name,
                        item,
                        "formula",
                        "output_formula",
                        "outputFormula",
                        "expression",
                    ),
                    "expression_language": self._mapping_string(
                        item_name,
                        item,
                        "expression_language",
                        "expressionLanguage",
                        "language",
                    ),
                    "function": function,
                    "conditions": condition_values,
                    "tuple_grain": self._normalise_tuple_grain_spec(
                        f"{item_name}.tuple_grain",
                        self._mapping_value(
                            item,
                            "tuple_grain",
                            "tupleGrain",
                            "output_grain",
                            "outputGrain",
                            "grain",
                        ),
                        default_iri=f"{output_iri_value}/grain",
                    ),
                }
            )
        return specs
    def _normalise_tuple_grain_spec(
        self,
        name: str,
        value: Any,
        *,
        default_iri: str,
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, MappingABC):
            raise DoxaBaseError(f"{name} must be an object")
        grain_iri = self._mapping_string(name, value, "iri", "id")
        components_value = self._mapping_value(
            value,
            "components",
            "grain_components",
            "grainComponents",
        )
        if components_value is None:
            raise DoxaBaseError(f"{name}.components must contain at least two entries")
        if isinstance(components_value, (str, MappingABC)):
            raise DoxaBaseError(f"{name}.components must be a list of objects")
        components = list(components_value)
        if len(components) < 2:
            raise DoxaBaseError(f"{name}.components must contain at least two entries")
        normalised_components: list[dict[str, Any]] = []
        for index, component in enumerate(components, start=1):
            component_name = f"{name}.components[{index}]"
            if not isinstance(component, MappingABC):
                raise DoxaBaseError(f"{component_name} must be an object")
            order = self._mapping_value(component, "order", "grain_order", "grainOrder")
            if order is None:
                order = index
            if not isinstance(order, int) or isinstance(order, bool) or order < 1:
                raise DoxaBaseError(f"{component_name}.order must be a positive integer")
            column = self._mapping_string(
                component_name,
                component,
                "column",
                "grain_column",
                "grainColumn",
            )
            dataset = self._mapping_string(
                component_name,
                component,
                "dataset",
                "grain_dataset",
                "grainDataset",
            )
            expression = self._mapping_string(
                component_name,
                component,
                "expression",
                "grain_expression",
                "grainExpression",
            )
            present_values = [
                value for value in (column, dataset, expression) if value is not None
            ]
            if not present_values:
                raise DoxaBaseError(
                    f"{component_name} requires exactly one of column, dataset, or expression"
                )
            if len(present_values) > 1:
                raise DoxaBaseError(
                    f"{component_name} must not mix column, dataset, and expression"
                )
            if column is not None:
                self._validate_relationship_column_resource(
                    f"{component_name}.column",
                    column,
                )
            if dataset is not None:
                self._resource_ref(f"{component_name}.dataset", dataset)
                self._validate_dataset_endpoint_resource(
                    f"{component_name}.dataset",
                    dataset,
                )
            component_iri = self._mapping_string(component_name, component, "iri", "id")
            normalised_components.append(
                {
                    "iri": (
                        self._required_iri(f"{component_name}.iri", component_iri)
                        if component_iri is not None
                        else f"{default_iri}/component/{index}"
                    ),
                    "label": self._mapping_string(component_name, component, "label"),
                    "description": self._mapping_string(
                        component_name,
                        component,
                        "description",
                        "comment",
                    ),
                    "order": order,
                    "role": self._mapping_string(
                        component_name,
                        component,
                        "role",
                        "grain_role",
                        "grainRole",
                    ),
                    "column": column,
                    "dataset": dataset,
                    "expression": expression,
                }
            )
        return {
            "iri": (
                self._required_iri(f"{name}.iri", grain_iri)
                if grain_iri is not None
                else default_iri
            ),
            "label": self._mapping_string(name, value, "label"),
            "description": self._mapping_string(name, value, "description", "comment"),
            "components": normalised_components,
        }
    def _mapping_list(
        self,
        name: str,
        values: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[Mapping[str, Any]]:
        if values is None:
            return []
        if isinstance(values, MappingABC):
            return [values]
        if isinstance(values, str):
            raise DoxaBaseError(f"{name} must be an object or list of objects")
        raw_values = list(values)
        for index, value in enumerate(raw_values, start=1):
            if not isinstance(value, MappingABC):
                raise DoxaBaseError(f"{name}[{index}] must be an object")
        return raw_values
    @staticmethod
    def _mapping_value(mapping: Mapping[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in mapping:
                return mapping[key]
        return None
    def _mapping_string(
        self,
        name: str,
        mapping: Mapping[str, Any],
        *keys: str,
        required: bool = False,
    ) -> str | None:
        value = self._mapping_value(mapping, *keys)
        if value is None:
            if required:
                joined_keys = " or ".join(keys)
                raise DoxaBaseError(f"{name} requires {joined_keys}")
            return None
        if not isinstance(value, str):
            joined_keys = " or ".join(keys)
            raise DoxaBaseError(f"{name}.{joined_keys} must be a string")
        cleaned = value.strip()
        if not cleaned:
            if required:
                joined_keys = " or ".join(keys)
                raise DoxaBaseError(f"{name} requires {joined_keys}")
            return None
        return cleaned
    def _delete_existing_asset_transform_triples(self, relationship_iri: str) -> None:
        condition_iris = self._objects(
            ["map"],
            relationship_iri,
            "rc:hasTransformCondition",
        )
        output_iris = self._objects(
            ["map"],
            relationship_iri,
            "rc:hasTransformOutput",
        )
        if not condition_iris and not output_iris:
            return

        def delete_subject_predicates(subject: str, predicates: Iterable[str]) -> None:
            predicate_values = list(dict.fromkeys(predicates))
            if not predicate_values:
                return
            placeholders = ",".join("?" for _ in predicate_values)
            self._conn.execute(
                f"""
                DELETE FROM quads
                WHERE graph = ?
                  AND subject = ?
                  AND predicate IN ({placeholders})
                """,
                ["map", subject, *predicate_values],
            )

        grain_iris: list[str] = []
        for output_iri in output_iris:
            output_grain_iris = self._objects(["map"], output_iri, "rc:outputGrain")
            grain_iris.extend(output_grain_iris)
            for dataset_iri in self._objects(["map"], output_iri, "rc:outputDataset"):
                for grain_iri in output_grain_iris:
                    self._conn.execute(
                        """
                        DELETE FROM quads
                        WHERE graph = ?
                          AND subject = ?
                          AND predicate = ?
                          AND object = ?
                        """,
                        [
                            "map",
                            dataset_iri,
                            self.expand_iri("rc:hasGrain"),
                            grain_iri,
                        ],
                    )

        component_iris: list[str] = []
        for grain_iri in grain_iris:
            component_iris.extend(
                self._objects(["map"], grain_iri, "rc:hasGrainComponent")
            )

        for component_iri in component_iris:
            delete_subject_predicates(
                component_iri,
                [
                    str(RDF.type),
                    str(RDFS.label),
                    str(RDFS.comment),
                    self.expand_iri("rc:grainOrder"),
                    self.expand_iri("rc:grainRole"),
                    self.expand_iri("rc:grainColumn"),
                    self.expand_iri("rc:grainDataset"),
                    self.expand_iri("rc:grainExpression"),
                ],
            )
        for grain_iri in grain_iris:
            delete_subject_predicates(
                grain_iri,
                [
                    str(RDF.type),
                    str(RDFS.label),
                    str(RDFS.comment),
                    self.expand_iri("rc:hasGrainComponent"),
                ],
            )
        for output_iri in output_iris:
            delete_subject_predicates(
                output_iri,
                [
                    str(RDF.type),
                    str(RDFS.label),
                    str(RDFS.comment),
                    self.expand_iri("rc:outputDataset"),
                    self.expand_iri("rc:outputRole"),
                    self.expand_iri("rc:outputFormula"),
                    self.expand_iri("rc:expressionLanguage"),
                    self.expand_iri("rc:outputFunction"),
                    self.expand_iri("rc:outputCondition"),
                    self.expand_iri("rc:outputGrain"),
                ],
            )
        for condition_iri in condition_iris:
            delete_subject_predicates(
                condition_iri,
                [
                    str(RDF.type),
                    str(RDFS.label),
                    str(RDFS.comment),
                    self.expand_iri("rc:conditionKind"),
                    self.expand_iri("rc:expressionText"),
                    self.expand_iri("rc:expressionLanguage"),
                    self.expand_iri("rc:appliesToDataset"),
                    self.expand_iri("rc:appliesToEndpoint"),
                ],
            )
        delete_subject_predicates(
            relationship_iri,
            [
                self.expand_iri("rc:hasTransformCondition"),
                self.expand_iri("rc:hasTransformOutput"),
            ],
        )
        self._conn.commit()
    def _impact_caveat_description(
        self,
        lookup_graphs: list[str],
        iri: str,
    ) -> CaveatDescription | None:
        caveat_type = self.expand_iri("rc:KnownCaveat")
        types = self._types_from_graphs(lookup_graphs, iri)
        has_caveat_shape = caveat_type in types or any(
            self._first_object(lookup_graphs, iri, predicate) is not None
            for predicate in ("rc:caveatDescription", "rc:impact", "rc:severity")
        )
        if not has_caveat_shape:
            return None
        return self._describe_caveat(iri, lookup_graphs, lookup_graphs)
    def _assertion_nearby_caveat_links(
        self,
        target_iris: Iterable[str],
        lookup_graphs: list[str],
    ) -> list[AssertionSupportCaveatLink]:
        all_graphs = self._expand_graphs(["all"])
        links: list[AssertionSupportCaveatLink] = []
        seen_links: set[tuple[str, str, str, str]] = set()
        caveat_type = self.expand_iri("rc:KnownCaveat")

        def add_link(
            caveat_iri: str,
            *,
            scope: str,
            route_type: str,
            route_label: str,
            via_iri: str,
            matched_iri: str,
        ) -> None:
            key = (caveat_iri, route_type, via_iri, matched_iri)
            if key in seen_links:
                return
            seen_links.add(key)
            links.append(
                AssertionSupportCaveatLink(
                    caveat=self._describe_caveat(
                        caveat_iri,
                        all_graphs,
                        lookup_graphs,
                    ),
                    scope=scope,
                    route_type=route_type,
                    route_label=route_label,
                    via_resource=self._resource_summary(
                        lookup_graphs,
                        via_iri,
                        display_label=True,
                    ),
                    matched_resource=self._resource_summary(
                        lookup_graphs,
                        matched_iri,
                        display_label=True,
                    ),
                )
            )

        for target_iri in target_iris:
            target_types = set(self._types_from_graphs(all_graphs, target_iri))
            if caveat_type in target_types or self._first_object(
                all_graphs,
                target_iri,
                "rc:caveatDescription",
            ):
                add_link(
                    target_iri,
                    scope="target_resource",
                    route_type="caveat_target_resource",
                    route_label="assertion target is a known caveat",
                    via_iri=target_iri,
                    matched_iri=target_iri,
                )
            for caveat_iri in self._objects(
                all_graphs,
                target_iri,
                "rc:hasKnownCaveat",
            ):
                add_link(
                    caveat_iri,
                    scope="direct_target",
                    route_type="target_has_known_caveat",
                    route_label="target resource has known caveat",
                    via_iri=target_iri,
                    matched_iri=target_iri,
                )
            owner_iri = self._first_owner_dataset_iri(all_graphs, target_iri)
            if owner_iri is not None:
                for caveat_iri in self._objects(
                    all_graphs,
                    owner_iri,
                    "rc:hasKnownCaveat",
                ):
                    add_link(
                        caveat_iri,
                        scope="owner_dataset",
                        route_type="owner_dataset_has_known_caveat",
                        route_label="owning dataset has known caveat",
                        via_iri=owner_iri,
                        matched_iri=target_iri,
                    )

        scope_order = {
            "target_resource": 0,
            "direct_target": 1,
            "owner_dataset": 2,
        }
        return sorted(
            links,
            key=lambda link: (
                scope_order.get(link.scope, 99),
                link.caveat.label or "",
                link.caveat.iri,
                link.via_resource.label or link.via_resource.iri,
                link.matched_resource.label or link.matched_resource.iri,
            ),
        )
    def _caveats_from_links(
        self,
        links: Iterable[AssertionSupportCaveatLink],
    ) -> list[CaveatDescription]:
        caveats: dict[str, CaveatDescription] = {}
        for link in links:
            caveats.setdefault(link.caveat.iri, link.caveat)
        return sorted(
            caveats.values(),
            key=lambda caveat: (caveat.label or "", caveat.iri),
        )
    def _describe_caveat(
        self,
        caveat_iri: str,
        data_graphs: list[str],
        lookup_graphs: list[str],
    ) -> CaveatDescription:
        severity = self._first_object(data_graphs, caveat_iri, "rc:severity")
        return CaveatDescription(
            iri=caveat_iri,
            label=self._display_label_from_graphs(lookup_graphs, caveat_iri),
            description=self._first_object(data_graphs, caveat_iri, "rc:caveatDescription")
            or self._description_from_graphs(lookup_graphs, caveat_iri),
            impact=self._first_object(data_graphs, caveat_iri, "rc:impact"),
            severity=self._optional_resource_summary(lookup_graphs, severity),
        )
    def _relationship_source_caveats(
        self,
        data_graphs: list[str],
        lookup_graphs: list[str],
        source_datasets: list[ResourceSummary],
        foreign_key_from: ResourceSummary | None,
        source_columns: list[ResourceSummary],
        group_by_columns: list[ResourceSummary],
        aggregated_columns: list[AggregatedColumnDescription],
    ) -> list[CaveatDescription]:
        source_resources: list[str] = []
        for source_dataset in source_datasets:
            source_resources.append(source_dataset.iri)
        if foreign_key_from is not None:
            source_resources.append(foreign_key_from.iri)
            if foreign_key_from.owning_dataset_iri is not None:
                source_resources.append(foreign_key_from.owning_dataset_iri)
        for column in (*source_columns, *group_by_columns):
            source_resources.append(column.iri)
            if column.owning_dataset_iri is not None:
                source_resources.append(column.owning_dataset_iri)
        for aggregated_column in aggregated_columns:
            for column in aggregated_column.source_columns:
                source_resources.append(column.iri)
                if column.owning_dataset_iri is not None:
                    source_resources.append(column.owning_dataset_iri)
            if aggregated_column.within_group_ordering is not None:
                source_resources.append(aggregated_column.within_group_ordering.iri)
                if (
                    aggregated_column.within_group_ordering.owning_dataset_iri
                    is not None
                ):
                    source_resources.append(
                        aggregated_column.within_group_ordering.owning_dataset_iri
                    )

        caveat_iris: list[str] = []
        for resource_iri in dict.fromkeys(source_resources):
            caveat_iris.extend(
                self._objects(data_graphs, resource_iri, "rc:hasKnownCaveat")
            )
        return [
            self._describe_caveat(caveat_iri, data_graphs, lookup_graphs)
            for caveat_iri in sorted(set(caveat_iris))
        ]
    def _bind_prefixes(self, graph: Graph) -> None:
        for prefix, namespace in PREFIXES.items():
            graph.bind(prefix, namespace)
    @staticmethod
    def _normalise_manifest_object_list(
        name: str,
        value: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        *,
        required: bool = False,
    ) -> list[Mapping[str, Any]]:
        if value is None:
            values: list[Mapping[str, Any]] = []
        elif isinstance(value, MappingABC):
            values = [value]
        elif isinstance(value, str):
            raise DoxaBaseError(f"{name} must be an object or a list of objects")
        else:
            values = list(value)
        if required and not values:
            raise DoxaBaseError(f"{name} must contain at least one object")
        for index, item in enumerate(values, start=1):
            if not isinstance(item, MappingABC):
                raise DoxaBaseError(f"{name}[{index}] must be an object")
        return values
    def _preflight_map_table_bundle(
        self,
        *,
        label: str | None,
        description: str | None,
        path_templates: Iterable[str] | str | None,
        row_count_snapshot: int | None,
        row_semantics: str | None,
        entity_key: str | None,
        schema_stability: str | None,
        layout_verification_status: str | None,
        layout_verification_note: str | None,
        caveats: Iterable[str] | str | None,
        companion_datasets: Iterable[str] | str | None,
        extra_types: Iterable[str] | str | None,
        storage_label: str | None,
        storage_description: str | None,
        route_roles: Iterable[str] | str | None,
        storage_protocol: str | None,
        access_mode: str | None,
        location_kind: str | None,
        storage_root: str | None,
        endpoint_profile: str | None,
        bucket_name: str | None,
        key_prefix: str | None,
        region: str | None,
        path_style_access: bool | None,
        credential_reference: str | None,
        storage_path_templates: Iterable[str] | str | None,
        storage_layout_verification_status: str | None,
        storage_layout_verification_note: str | None,
        physical_layout_label: str | None,
        physical_layout_description: str | None,
        file_format: str | None,
        compression_codec: str | None,
        physical_layout_verification_status: str | None,
        physical_layout_verification_note: str | None,
    ) -> None:
        for name, value in (
            ("label", label),
            ("description", description),
            ("layout_verification_note", layout_verification_note),
            ("storage_label", storage_label),
            ("storage_description", storage_description),
            ("storage_root", storage_root),
            ("endpoint_profile", endpoint_profile),
            ("bucket_name", bucket_name),
            ("key_prefix", key_prefix),
            ("region", region),
            ("credential_reference", credential_reference),
            (
                "storage_layout_verification_note",
                storage_layout_verification_note,
            ),
            ("physical_layout_label", physical_layout_label),
            ("physical_layout_description", physical_layout_description),
            (
                "physical_layout_verification_note",
                physical_layout_verification_note,
            ),
        ):
            self._preflight_optional_string(name, value)
        self._preflight_string_values("path_templates", path_templates)
        self._ensure_non_negative("row_count_snapshot", row_count_snapshot)
        if row_semantics is not None:
            self._controlled_resource_ref(
                "row_semantics",
                row_semantics,
                ROW_SEMANTICS_TYPES,
            )
        if entity_key is not None:
            self._resource_ref("entity_key", entity_key)
        if schema_stability is not None:
            self._controlled_resource_ref(
                "schema_stability",
                schema_stability,
                SCHEMA_STABILITY_LEVELS,
            )
        if layout_verification_status is not None:
            self._controlled_resource_ref(
                "layout_verification_status",
                layout_verification_status,
                LAYOUT_VERIFICATION_STATUSES,
            )
        self._validate_resource_values(
            "caveats",
            self._preflight_string_values("caveats", caveats),
        )
        self._validate_resource_values(
            "companion_datasets",
            self._preflight_string_values("companion_datasets", companion_datasets),
        )
        self._validate_resource_values(
            "extra_types",
            self._preflight_string_values("extra_types", extra_types),
        )
        self._validate_resource_values(
            "route_roles",
            self._preflight_string_values("route_roles", route_roles),
        )
        if storage_protocol is not None:
            self._resource_ref("storage_protocol", storage_protocol)
        if access_mode is not None:
            self._resource_ref("access_mode", access_mode)
        self._storage_location_kind(location_kind)
        if path_style_access is not None and not isinstance(path_style_access, bool):
            raise DoxaBaseError("path_style_access must be a boolean")
        if storage_layout_verification_status is not None:
            self._controlled_resource_ref(
                "storage_layout_verification_status",
                storage_layout_verification_status,
                LAYOUT_VERIFICATION_STATUSES,
            )
        self._preflight_string_values(
            "storage_path_templates",
            storage_path_templates,
        )
        if file_format is not None:
            self._resource_ref("file_format", file_format)
        if compression_codec is not None:
            self._resource_ref("compression_codec", compression_codec)
        if physical_layout_verification_status is not None:
            self._controlled_resource_ref(
                "physical_layout_verification_status",
                physical_layout_verification_status,
                LAYOUT_VERIFICATION_STATUSES,
            )
    def _storage_location_kind(self, value: str | None) -> str | None:
        if value is None:
            return None
        kind = value.strip().lower()
        if not kind:
            return None
        if kind == "bucket":
            return "prefix"
        allowed = {"object", "directory", "prefix", "connection"}
        if kind not in allowed:
            raise DoxaBaseError(
                "location_kind must be one of: object, directory, prefix, "
                "connection; 'bucket' is accepted as an input alias for "
                "'prefix'. Do not use 'local_path': local filesystem belongs in "
                "storage_protocol='rc:LocalFilesystemStorage', while "
                "location_kind describes the storage_root shape. Use 'object' "
                "when the root is the exact file/object/location, or "
                "'directory' when it is a local folder."
            )
        return kind
    def _string_values(
        self,
        name: str,
        value: Iterable[str] | str | None,
        *,
        required: bool = False,
    ) -> list[str]:
        if value is None:
            values: list[str] = []
        elif isinstance(value, str):
            values = [value]
        else:
            values = list(value)
        cleaned = [item.strip() for item in values if item.strip()]
        if required and not cleaned:
            raise DoxaBaseError(f"{name} must contain at least one non-empty value")
        return cleaned
