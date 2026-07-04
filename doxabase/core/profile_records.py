"""Profile recording (dataset, column, bundle, domain network).

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via ProfileRecordsMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class ProfileRecordsMixin:
    def record_dataset_profile(
        self,
        dataset_iri: str,
        *,
        summary: str,
        observed_at: datetime | str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: Iterable[str] | str | None = None,
        sample_size: int | None = None,
        sample_scope: str | None = None,
        sample_method: str | None = None,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
        value_frequencies: Iterable[Mapping[str, Any]] | None = None,
        profile_metrics: Iterable[Mapping[str, Any]] | None = None,
        update_map_snapshot: bool = True,
        allow_sampled_row_count_snapshot: bool = False,
        map_label: str | None = None,
        map_description: str | None = None,
        is_table: bool | None = None,
        pattern_summary: str | None = None,
        pattern_text: str | None = None,
        pattern_rationale: str | None = None,
        pattern_confidence: str | None = "rc:MediumConfidence",
        pattern_status: str | None = "rc:Tentative",
        pattern_stability: str | None = "rc:EmergingPattern",
        pattern_map_implications: Iterable[str] | str | None = None,
        observation_iri: str | None = None,
        evidence_iri: str | None = None,
        pattern_iri: str | None = None,
    ) -> DatasetProfileRecord:
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        profile_metric_items = (
            list(profile_metrics) if profile_metrics is not None else None
        )
        should_record_pattern = self._profile_pattern_requested(
            pattern_summary,
            pattern_text,
            pattern_rationale,
        )
        pattern_implication_values: list[str] | None = None
        if should_record_pattern:
            pattern_implication_values = self._preflight_profile_pattern(
                primary_resource_iri=dataset_value,
                pattern_map_implications=pattern_map_implications,
                profile_metric_sets=(("profile_metrics", profile_metric_items),),
                pattern_confidence=pattern_confidence,
                pattern_status=pattern_status,
                pattern_stability=pattern_stability,
            )

        observation = self.record_observation(
            summary=summary,
            observation_type="profile",
            observed_asset=dataset_value,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method,
            row_count=row_count,
            null_count=null_count,
            distinct_count=distinct_count,
            value_frequencies=value_frequencies,
            profile_metrics=profile_metric_items,
            observation_iri=observation_iri,
            evidence_iri=evidence_iri,
        )

        map_dataset: MapResourceRecord | None = None
        row_count_snapshot = self._profile_row_count_snapshot_value(
            row_count=row_count,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method,
            allow_sampled_row_count_snapshot=allow_sampled_row_count_snapshot,
        )
        should_update_map = update_map_snapshot and (
            row_count_snapshot is not None
            or map_label is not None
            or map_description is not None
            or is_table is not None
        )
        if should_update_map:
            map_dataset = self.record_map_dataset(
                dataset_value,
                label=map_label,
                description=map_description,
                is_table=is_table,
                row_count_snapshot=row_count_snapshot,
            )

        pattern: PatternRecord | None = None
        if should_record_pattern:
            assert pattern_summary is not None
            assert pattern_text is not None
            assert pattern_rationale is not None
            assert pattern_implication_values is not None
            pattern = self.record_pattern(
                summary=pattern_summary,
                pattern_text=pattern_text,
                rationale=pattern_rationale,
                pattern_targets=[dataset_value],
                supporting_observations=[observation.observation_iri],
                evidence_iri=observation.evidence_iri,
                confidence=pattern_confidence,
                pattern_status=pattern_status,
                pattern_stability=pattern_stability,
                map_implications=pattern_implication_values,
                pattern_iri=pattern_iri,
            )

        return DatasetProfileRecord(
            dataset_iri=dataset_value,
            observation=observation,
            map_dataset=map_dataset,
            pattern=pattern,
        )
    def record_column_profile(
        self,
        column_iri: str,
        *,
        column_name: str,
        summary: str,
        table_iri: str | None = None,
        observed_at: datetime | str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: Iterable[str] | str | None = None,
        sample_size: int | None = None,
        sample_scope: str | None = None,
        sample_method: str | None = None,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
        value_frequencies: Iterable[Mapping[str, Any]] | None = None,
        profile_metrics: Iterable[Mapping[str, Any]] | None = None,
        update_map_column: bool = True,
        map_label: str | None = None,
        map_description: str | None = None,
        physical_type: str | None = None,
        value_type: str | None = None,
        nullable: bool | None = None,
        pattern_summary: str | None = None,
        pattern_text: str | None = None,
        pattern_rationale: str | None = None,
        pattern_confidence: str | None = "rc:MediumConfidence",
        pattern_status: str | None = "rc:Tentative",
        pattern_stability: str | None = "rc:EmergingPattern",
        pattern_map_implications: Iterable[str] | str | None = None,
        observation_iri: str | None = None,
        evidence_iri: str | None = None,
        pattern_iri: str | None = None,
    ) -> ColumnProfileRecord:
        column_value = self._required_iri("column_iri", column_iri)
        profile_metric_items = (
            list(profile_metrics) if profile_metrics is not None else None
        )
        table_value = (
            self._required_iri("table_iri", table_iri)
            if table_iri is not None
            else None
        )
        should_record_pattern = self._profile_pattern_requested(
            pattern_summary,
            pattern_text,
            pattern_rationale,
        )
        pattern_implication_values: list[str] | None = None
        if should_record_pattern:
            pattern_implication_values = self._preflight_profile_pattern(
                primary_resource_iri=column_value,
                pattern_map_implications=pattern_map_implications,
                profile_metric_sets=(("profile_metrics", profile_metric_items),),
                profile_value_type_fields=(("value_type", value_type),),
                pattern_confidence=pattern_confidence,
                pattern_status=pattern_status,
                pattern_stability=pattern_stability,
            )

        observation = self.record_observation(
            summary=summary,
            observation_type="profile",
            observed_asset=table_value,
            observed_column=column_value,
            observed_column_name=column_name,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method,
            row_count=row_count,
            null_count=null_count,
            distinct_count=distinct_count,
            value_frequencies=value_frequencies,
            profile_metrics=profile_metric_items,
            observed_physical_type=physical_type,
            observed_value_type=value_type,
            observation_iri=observation_iri,
            evidence_iri=evidence_iri,
        )

        map_column: MapResourceRecord | None = None
        should_update_map = update_map_column and (
            table_value is not None
            or map_label is not None
            or map_description is not None
            or physical_type is not None
            or value_type is not None
            or nullable is not None
        )
        if should_update_map:
            map_column = self.record_map_column(
                column_value,
                column_name=column_name,
                table_iri=table_value,
                label=map_label,
                description=map_description,
                physical_type=physical_type,
                value_type=value_type,
                nullable=nullable,
            )

        pattern: PatternRecord | None = None
        if should_record_pattern:
            assert pattern_summary is not None
            assert pattern_text is not None
            assert pattern_rationale is not None
            assert pattern_implication_values is not None
            pattern = self.record_pattern(
                summary=pattern_summary,
                pattern_text=pattern_text,
                rationale=pattern_rationale,
                pattern_targets=[column_value],
                supporting_observations=[observation.observation_iri],
                evidence_iri=observation.evidence_iri,
                confidence=pattern_confidence,
                pattern_status=pattern_status,
                pattern_stability=pattern_stability,
                map_implications=pattern_implication_values,
                pattern_iri=pattern_iri,
            )

        return ColumnProfileRecord(
            column_iri=column_value,
            table_iri=table_value,
            observation=observation,
            map_column=map_column,
            pattern=pattern,
        )
    def record_profile_bundle(
        self,
        dataset_iri: str,
        *,
        dataset_summary: str,
        column_profiles: Iterable[Mapping[str, Any]] | None = None,
        observed_at: datetime | str | None = None,
        observed_by: str | None = None,
        evidence_summary: str | None = None,
        evidence_sources: Iterable[str] | str | None = None,
        sample_size: int | None = None,
        sample_scope: str | None = None,
        sample_method: str | None = None,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
        value_frequencies: Iterable[Mapping[str, Any]] | None = None,
        profile_metrics: Iterable[Mapping[str, Any]] | None = None,
        update_map_snapshot: bool = True,
        allow_sampled_row_count_snapshot: bool = False,
        map_label: str | None = None,
        map_description: str | None = None,
        is_table: bool | None = None,
        pattern_summary: str | None = None,
        pattern_text: str | None = None,
        pattern_rationale: str | None = None,
        pattern_confidence: str | None = "rc:MediumConfidence",
        pattern_status: str | None = "rc:Tentative",
        pattern_stability: str | None = "rc:EmergingPattern",
        pattern_map_implications: Iterable[str] | str | None = None,
        pattern_support_scope: TypingLiteral["dataset_profile", "all_profiles"]
        | str = "dataset_profile",
        shared_evidence_iri: str | None = None,
        column_defaults: Mapping[str, Any] | None = None,
    ) -> ProfileBundleRecord:
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        profile_metric_items = (
            list(profile_metrics) if profile_metrics is not None else None
        )
        pattern_support_scope_value = self._profile_bundle_pattern_support_scope(
            pattern_support_scope
        )
        allowed_column_keys = {
            "column_iri",
            "column_name",
            "summary",
            "table_iri",
            "observed_at",
            "observed_by",
            "evidence_summary",
            "evidence_sources",
            "sample_size",
            "sample_scope",
            "sample_method",
            "row_count",
            "null_count",
            "distinct_count",
            "value_frequencies",
            "profile_metrics",
            "update_map_column",
            "map_label",
            "map_description",
            "physical_type",
            "value_type",
            "nullable",
            "pattern_summary",
            "pattern_text",
            "pattern_rationale",
            "pattern_confidence",
            "pattern_status",
            "pattern_stability",
            "pattern_map_implications",
            "observation_iri",
            "evidence_iri",
            "pattern_iri",
        }
        required_column_keys = {"column_iri", "column_name", "summary"}

        shared_column_defaults: dict[str, Any] = {
            "table_iri": dataset_value,
            "observed_at": observed_at,
            "observed_by": observed_by,
            "evidence_summary": evidence_summary,
            "evidence_sources": evidence_sources,
            "sample_size": sample_size,
            "sample_scope": sample_scope,
            "sample_method": sample_method,
            "evidence_iri": shared_evidence_iri,
        }
        merged_defaults = {
            key: value
            for key, value in shared_column_defaults.items()
            if value is not None
        }
        if column_defaults is not None:
            merged_defaults.update(dict(column_defaults))
        unknown_defaults = sorted(set(merged_defaults) - allowed_column_keys)
        if unknown_defaults:
            raise DoxaBaseError(
                "column_defaults contains unsupported record_column_profile "
                f"field(s): {', '.join(unknown_defaults)}"
            )
        should_record_pattern = self._profile_pattern_requested(
            pattern_summary,
            pattern_text,
            pattern_rationale,
        )

        prepared_column_profiles: list[dict[str, Any]] = []
        for index, profile_mapping in enumerate(column_profiles or []):
            try:
                profile_values = dict(profile_mapping)
            except (TypeError, ValueError) as exc:
                raise DoxaBaseError(
                    f"column_profiles[{index}] must be a mapping"
                ) from exc
            unknown_keys = sorted(set(profile_values) - allowed_column_keys)
            if unknown_keys:
                raise DoxaBaseError(
                    f"column_profiles[{index}] contains unsupported "
                    f"record_column_profile field(s): {', '.join(unknown_keys)}"
                )
            column_kwargs = {**merged_defaults, **profile_values}
            if column_kwargs.get("profile_metrics") is not None:
                column_kwargs["profile_metrics"] = list(
                    column_kwargs["profile_metrics"]
                )
            missing_keys = sorted(
                key for key in required_column_keys if not column_kwargs.get(key)
            )
            if missing_keys:
                raise DoxaBaseError(
                    f"column_profiles[{index}] is missing required field(s): "
                    f"{', '.join(missing_keys)}"
                )
            self._preflight_profile_bundle_column(index, column_kwargs)
            prepared_column_profiles.append(column_kwargs)

        bundle_pattern_implications: list[str] | None = None
        if should_record_pattern:
            metric_sets: list[tuple[str, Iterable[Mapping[str, Any]] | None]] = [
                ("profile_metrics", profile_metric_items)
            ]
            value_type_fields: list[tuple[str, str | None]] = []
            if pattern_support_scope_value == "all_profiles":
                metric_sets.extend(
                    (
                        f"column_profiles[{index}].profile_metrics",
                        column_kwargs.get("profile_metrics"),
                    )
                    for index, column_kwargs in enumerate(prepared_column_profiles)
                )
                value_type_fields.extend(
                    (
                        f"column_profiles[{index}].value_type",
                        column_kwargs.get("value_type"),
                    )
                    for index, column_kwargs in enumerate(prepared_column_profiles)
                )
            bundle_pattern_implications = self._preflight_profile_pattern(
                primary_resource_iri=dataset_value,
                pattern_map_implications=pattern_map_implications,
                profile_metric_sets=metric_sets,
                profile_value_type_fields=value_type_fields,
                pattern_confidence=pattern_confidence,
                pattern_status=pattern_status,
                pattern_stability=pattern_stability,
            )

        self._preflight_profile_bundle_evidence_summaries(
            shared_evidence_iri=shared_evidence_iri,
            dataset_evidence_summary=evidence_summary,
            column_profiles=prepared_column_profiles,
        )

        dataset_profile = self.record_dataset_profile(
            dataset_value,
            summary=dataset_summary,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method,
            row_count=row_count,
            null_count=null_count,
            distinct_count=distinct_count,
            value_frequencies=value_frequencies,
            profile_metrics=profile_metric_items,
            update_map_snapshot=update_map_snapshot,
            allow_sampled_row_count_snapshot=allow_sampled_row_count_snapshot,
            map_label=map_label,
            map_description=map_description,
            is_table=is_table,
            pattern_summary=(
                pattern_summary
                if pattern_support_scope_value == "dataset_profile"
                else None
            ),
            pattern_text=(
                pattern_text
                if pattern_support_scope_value == "dataset_profile"
                else None
            ),
            pattern_rationale=(
                pattern_rationale
                if pattern_support_scope_value == "dataset_profile"
                else None
            ),
            pattern_confidence=pattern_confidence,
            pattern_status=pattern_status,
            pattern_stability=pattern_stability,
            pattern_map_implications=(
                bundle_pattern_implications
                if pattern_support_scope_value == "dataset_profile"
                else None
            ),
            evidence_iri=shared_evidence_iri,
        )

        recorded_columns: list[ColumnProfileRecord] = []
        for column_kwargs in prepared_column_profiles:
            recorded_columns.append(
                self.record_column_profile(**column_kwargs)  # type: ignore[arg-type]
            )

        if should_record_pattern and pattern_support_scope_value == "all_profiles":
            assert pattern_summary is not None
            assert pattern_text is not None
            assert pattern_rationale is not None
            assert bundle_pattern_implications is not None
            pattern = self.record_pattern(
                summary=pattern_summary,
                pattern_text=pattern_text,
                rationale=pattern_rationale,
                pattern_targets=[dataset_value],
                supporting_observations=[
                    dataset_profile.observation.observation_iri,
                    *(
                        column_profile.observation.observation_iri
                        for column_profile in recorded_columns
                    ),
                ],
                evidence_iri=dataset_profile.observation.evidence_iri,
                confidence=pattern_confidence,
                pattern_status=pattern_status,
                pattern_stability=pattern_stability,
                map_implications=bundle_pattern_implications,
            )
            dataset_profile = replace(dataset_profile, pattern=pattern)

        return ProfileBundleRecord(
            dataset_iri=dataset_value,
            shared_evidence_iri=shared_evidence_iri,
            dataset_profile=dataset_profile,
            column_profiles=recorded_columns,
            handoff_entrypoints=self._profile_bundle_handoff_entrypoints(
                dataset_iri=dataset_value,
                shared_evidence_iri=shared_evidence_iri,
                dataset_profile=dataset_profile,
                column_profiles=recorded_columns,
            ),
        )
    def record_domain_network_profile(
        self,
        dataset_iri: str,
        *,
        summary: str,
        evidence_summary: str,
        sample_size: int,
        sample_scope: str,
        sample_method: str,
        extraction_method: str,
        coverage_counts: Iterable[Mapping[str, Any]],
        observed_at: datetime | str | None = None,
        observed_by: str | None = None,
        evidence_sources: Iterable[str] | str | None = None,
        evidence_iri: str | None = None,
        coverage_counts_exhaustive: bool = False,
        domain_pair_counts: Iterable[Mapping[str, Any]] | None = None,
        sender_domain_counts: Iterable[Mapping[str, Any]] | None = None,
        recipient_domain_counts: Iterable[Mapping[str, Any]] | None = None,
        domain_pair_min_count: int = 5,
        allow_low_frequency_domain_pairs: bool = False,
        analysis_view_iri: str | None = None,
        analysis_view_label: str | None = None,
        analysis_view_description: str | None = None,
        analysis_view_row_count_snapshot: int | None = None,
        analysis_view_query_text: str | None = None,
        analysis_view_query_language: str | None = None,
        analysis_view_query_engine: str | None = None,
        caveat_iri: str | None = None,
        caveat_label: str | None = None,
        caveat_description: str | None = None,
        caveat_severity: str | None = "rc:Moderate",
        pattern_summary: str | None = None,
        pattern_text: str | None = None,
        pattern_rationale: str | None = None,
        pattern_confidence: str | None = "rc:MediumConfidence",
        pattern_status: str | None = "rc:Tentative",
        pattern_stability: str | None = "rc:EmergingPattern",
    ) -> DomainNetworkProfileRecord:
        dataset_value = self._required_iri("dataset_iri", dataset_iri)
        evidence_value = (
            self._required_iri("evidence_iri", evidence_iri)
            if evidence_iri is not None
            else self._mint_iri("evidence")
        )
        self._ensure_positive_int("sample_size", sample_size)
        self._ensure_positive_int("domain_pair_min_count", domain_pair_min_count)
        if not isinstance(summary, str) or not summary.strip():
            raise DoxaBaseError("summary must not be empty")
        if not isinstance(evidence_summary, str) or not evidence_summary.strip():
            raise DoxaBaseError("evidence_summary must not be empty")
        if not isinstance(sample_scope, str) or not sample_scope.strip():
            raise DoxaBaseError("sample_scope must not be empty")
        if not isinstance(sample_method, str) or not sample_method.strip():
            raise DoxaBaseError("sample_method must not be empty")
        if not isinstance(extraction_method, str):
            raise DoxaBaseError("extraction_method must not be empty")
        extraction_method_value = extraction_method.strip()
        if not extraction_method_value:
            raise DoxaBaseError("extraction_method must not be empty")
        for name, value in (
            ("observed_by", observed_by),
            ("evidence_iri", evidence_iri),
            ("analysis_view_iri", analysis_view_iri),
            ("analysis_view_label", analysis_view_label),
            ("analysis_view_description", analysis_view_description),
            ("analysis_view_query_text", analysis_view_query_text),
            ("analysis_view_query_language", analysis_view_query_language),
            ("analysis_view_query_engine", analysis_view_query_engine),
            ("caveat_iri", caveat_iri),
            ("caveat_label", caveat_label),
            ("caveat_description", caveat_description),
            ("caveat_severity", caveat_severity),
            ("pattern_summary", pattern_summary),
            ("pattern_text", pattern_text),
            ("pattern_rationale", pattern_rationale),
            ("pattern_confidence", pattern_confidence),
            ("pattern_status", pattern_status),
            ("pattern_stability", pattern_stability),
        ):
            self._preflight_optional_string(name, value)

        coverage_values = self._domain_network_frequency_values(
            "coverage_counts",
            coverage_counts,
            value_fields=("bucket", "value", "classification"),
        )
        if not coverage_values:
            raise DoxaBaseError("coverage_counts must contain at least one bucket")
        coverage_total = sum(item["frequency"] for item in coverage_values)
        if coverage_counts_exhaustive and coverage_total != sample_size:
            raise DoxaBaseError(
                "coverage_counts are marked exhaustive but their frequencies "
                f"sum to {coverage_total}, not sample_size {sample_size}"
            )
        pair_values = self._domain_network_pair_frequency_values(
            domain_pair_counts,
            min_count=domain_pair_min_count,
            allow_low_frequency=allow_low_frequency_domain_pairs,
        )
        sender_values = self._domain_network_frequency_values(
            "sender_domain_counts",
            sender_domain_counts,
            value_fields=("domain", "value", "sender_domain"),
            required=False,
        )
        recipient_values = self._domain_network_frequency_values(
            "recipient_domain_counts",
            recipient_domain_counts,
            value_fields=("domain", "value", "recipient_domain"),
            required=False,
        )
        self._preflight_evidence_summary_reuse(
            evidence_value,
            evidence_summary,
        )

        caveat_requested = caveat_description is not None or caveat_iri is not None
        caveat_value = (
            self._required_iri("caveat_iri", caveat_iri)
            if caveat_iri is not None
            else f"{dataset_value}/domain-network-caveat"
            if caveat_requested
            else None
        )
        if caveat_requested and caveat_severity is not None:
            self._controlled_resource_ref(
                "caveat_severity",
                caveat_severity,
                CAVEAT_SEVERITY_LEVELS,
            )
        analysis_view_requested = any(
            value is not None
            for value in (
                analysis_view_iri,
                analysis_view_label,
                analysis_view_description,
                analysis_view_row_count_snapshot,
                analysis_view_query_text,
                analysis_view_query_language,
                analysis_view_query_engine,
            )
        )
        analysis_view_value = (
            self._required_iri("analysis_view_iri", analysis_view_iri)
            if analysis_view_iri is not None
            else f"{dataset_value}/domain-network-analysis-view"
            if analysis_view_requested
            else None
        )
        self._ensure_non_negative(
            "analysis_view_row_count_snapshot",
            analysis_view_row_count_snapshot,
        )
        if analysis_view_query_text is not None and not analysis_view_query_text.strip():
            raise DoxaBaseError("analysis_view_query_text must not be empty")
        should_record_pattern = self._profile_pattern_requested(
            pattern_summary,
            pattern_text,
            pattern_rationale,
        )
        pattern_implications = [
            target for target in (caveat_value, analysis_view_value) if target is not None
        ]
        if should_record_pattern:
            self._preflight_profile_pattern(
                primary_resource_iri=dataset_value,
                pattern_map_implications=pattern_implications,
                profile_metric_sets=(),
                pattern_confidence=pattern_confidence,
                pattern_status=pattern_status,
                pattern_stability=pattern_stability,
            )

        caveat_record: MapResourceRecord | None = None
        if caveat_requested:
            assert caveat_value is not None
            caveat_record = self.record_map_caveat(
                caveat_value,
                label=caveat_label,
                description=(
                    caveat_description
                    or (
                        "Domain-network interpretation depends on sender and "
                        "recipient extraction coverage; reviewed aggregate "
                        "counts do not prove missing communications are absent."
                    )
                ),
                severity=caveat_severity,
                targets=[dataset_value],
            )

        analysis_view_record: MapResourceRecord | None = None
        if analysis_view_requested:
            assert analysis_view_value is not None
            analysis_view_record = self.record_map_analysis_view(
                analysis_view_value,
                label=analysis_view_label,
                description=analysis_view_description,
                source_datasets=[dataset_value],
                row_count_snapshot=analysis_view_row_count_snapshot,
                caveats=[caveat_value] if caveat_value is not None else None,
                denominator_description=sample_scope,
                denominator_row_count_snapshot=sample_size,
                denominator_basis=extraction_method_value,
                query_text=analysis_view_query_text,
                query_language=analysis_view_query_language,
                query_engine=analysis_view_query_engine,
            )

        sample_method_value = (
            f"{sample_method.strip()} Extraction method: {extraction_method_value}"
        )
        coverage_profile = self.record_dataset_profile(
            dataset_value,
            summary=summary,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            evidence_iri=evidence_value,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method_value,
            row_count=sample_size if coverage_counts_exhaustive else None,
            value_frequencies=coverage_values,
            update_map_snapshot=False,
        )
        domain_pair_profile = self._record_optional_domain_network_profile(
            dataset_value,
            summary="Domain pair aggregate counts for network profiling.",
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            evidence_iri=evidence_value,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method_value,
            value_frequencies=pair_values,
        )
        sender_domain_profile = self._record_optional_domain_network_profile(
            dataset_value,
            summary="Sender domain aggregate counts for network profiling.",
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            evidence_iri=evidence_value,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method_value,
            value_frequencies=sender_values,
        )
        recipient_domain_profile = self._record_optional_domain_network_profile(
            dataset_value,
            summary="Recipient domain aggregate counts for network profiling.",
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            evidence_iri=evidence_value,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method_value,
            value_frequencies=recipient_values,
        )

        profile_records = [
            profile
            for profile in (
                coverage_profile,
                domain_pair_profile,
                sender_domain_profile,
                recipient_domain_profile,
            )
            if profile is not None
        ]
        profile_observation_iris = [
            profile.observation.observation_iri for profile in profile_records
        ]
        pattern: PatternRecord | None = None
        if should_record_pattern:
            assert pattern_summary is not None
            assert pattern_text is not None
            assert pattern_rationale is not None
            pattern = self.record_pattern(
                summary=pattern_summary,
                pattern_text=pattern_text,
                rationale=pattern_rationale,
                pattern_targets=[
                    target
                    for target in (analysis_view_value, dataset_value)
                    if target is not None
                ],
                supporting_observations=profile_observation_iris,
                evidence_iri=evidence_value,
                confidence=pattern_confidence,
                pattern_status=pattern_status,
                pattern_stability=pattern_stability,
                map_implications=pattern_implications,
            )

        suggested_next_actions = [
            SuggestedNextAction(
                action_label="Describe profiled dataset",
                tool_name="describe_dataset",
                mcp_tool_name="doxabase.describe_dataset",
                arguments={"iri": dataset_value},
                reason=(
                    "Inspect the dataset with the recorded domain-network "
                    "profile observations and map caveats."
                ),
                call=self._suggested_call_string(
                    "describe_dataset",
                    {"iri": dataset_value},
                ),
            ),
            SuggestedNextAction(
                action_label="Inspect domain-network profile run",
                tool_name="describe_profile_run",
                mcp_tool_name="doxabase.describe_profile_run",
                arguments={
                    "dataset_iri": dataset_value,
                    "evidence_iri": evidence_value,
                },
                reason=(
                    "Review the shared evidence run containing coverage, "
                    "domain-pair, and domain-frequency aggregates."
                ),
                call=self._suggested_call_string(
                    "describe_profile_run",
                    {"dataset_iri": dataset_value, "evidence_iri": evidence_value},
                ),
            ),
        ]
        if analysis_view_value is not None:
            suggested_next_actions.append(
                SuggestedNextAction(
                    action_label="Describe domain-network analysis view",
                    tool_name="describe_analysis_view",
                    mcp_tool_name="doxabase.describe_analysis_view",
                    arguments={"iri": analysis_view_value},
                    reason=(
                        "Inspect the named population and denominator for the "
                        "domain-network aggregate profile."
                    ),
                    call=self._suggested_call_string(
                        "describe_analysis_view",
                        {"iri": analysis_view_value},
                    ),
                )
            )
        if pattern is not None:
            suggested_next_actions.append(
                SuggestedNextAction(
                    action_label="Describe domain-network coverage pattern",
                    tool_name="describe_pattern",
                    mcp_tool_name="doxabase.describe_pattern",
                    arguments={"iri": pattern.pattern_iri},
                    reason=(
                        "Review the synthesis that explains how extraction "
                        "coverage affects network interpretation."
                    ),
                    call=self._suggested_call_string(
                        "describe_pattern",
                        {"iri": pattern.pattern_iri},
                    ),
                )
            )
        return DomainNetworkProfileRecord(
            dataset_iri=dataset_value,
            evidence_iri=evidence_value,
            analysis_view=analysis_view_record,
            caveat=caveat_record,
            coverage_profile=coverage_profile,
            domain_pair_profile=domain_pair_profile,
            sender_domain_profile=sender_domain_profile,
            recipient_domain_profile=recipient_domain_profile,
            pattern=pattern,
            profile_observation_iris=profile_observation_iris,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[
                action.call for action in suggested_next_actions if action.call
            ],
        )
    def _domain_network_frequency_values(
        self,
        name: str,
        values: Iterable[Mapping[str, Any]] | None,
        *,
        value_fields: tuple[str, ...],
        required: bool = True,
    ) -> list[dict[str, Any]]:
        if values is None:
            if required:
                raise DoxaBaseError(f"{name} must contain at least one bucket")
            return []
        items = list(values)
        if required and not items:
            raise DoxaBaseError(f"{name} must contain at least one bucket")
        frequencies: list[dict[str, Any]] = []
        for index, item in enumerate(items, start=1):
            if not isinstance(item, MappingABC):
                raise DoxaBaseError(f"{name}[{index}] must be an object")
            value = self._domain_network_spec_value(
                name,
                index,
                item,
                value_fields=value_fields,
            )
            frequency = self._domain_network_frequency(name, index, item)
            frequencies.append({"value": value, "frequency": frequency})
        return frequencies
    def _domain_network_pair_frequency_values(
        self,
        values: Iterable[Mapping[str, Any]] | None,
        *,
        min_count: int,
        allow_low_frequency: bool,
    ) -> list[dict[str, Any]]:
        if values is None:
            return []
        frequencies: list[dict[str, Any]] = []
        for index, item in enumerate(list(values), start=1):
            if not isinstance(item, MappingABC):
                raise DoxaBaseError(f"domain_pair_counts[{index}] must be an object")
            if item.get("value") is not None:
                pair_value = self._domain_network_spec_value(
                    "domain_pair_counts",
                    index,
                    item,
                    value_fields=("value",),
                )
            else:
                sender = self._domain_network_spec_value(
                    "domain_pair_counts",
                    index,
                    item,
                    value_fields=("sender_domain",),
                )
                recipient = self._domain_network_spec_value(
                    "domain_pair_counts",
                    index,
                    item,
                    value_fields=("recipient_domain",),
                )
                pair_value = f"{sender} -> {recipient}"
            frequency = self._domain_network_frequency(
                "domain_pair_counts",
                index,
                item,
            )
            if frequency < min_count and not allow_low_frequency:
                raise DoxaBaseError(
                    f"domain_pair_counts[{index}] frequency {frequency} is "
                    f"below domain_pair_min_count {min_count}; pass "
                    "allow_low_frequency_domain_pairs=True only after privacy "
                    "review confirms the aggregate is safe to preserve."
                )
            frequencies.append({"value": pair_value, "frequency": frequency})
        return frequencies
    def _domain_network_spec_value(
        self,
        name: str,
        index: int,
        item: Mapping[Any, Any],
        *,
        value_fields: tuple[str, ...],
    ) -> str:
        field_used = None
        value = None
        for field in value_fields:
            if item.get(field) is not None:
                field_used = field
                value = item.get(field)
                break
        field_text = " or ".join(value_fields)
        if not isinstance(value, str) or not value.strip():
            raise DoxaBaseError(
                f"{name}[{index}] must include a non-empty string {field_text}"
            )
        value_text = value.strip()
        self._reject_domain_network_raw_address(
            f"{name}[{index}].{field_used}",
            value_text,
        )
        return value_text
    def _domain_network_frequency(
        self,
        name: str,
        index: int,
        item: Mapping[Any, Any],
    ) -> int:
        field = "frequency" if "frequency" in item else "count"
        value = item.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            raise DoxaBaseError(f"{name}[{index}].{field} must be an integer")
        self._ensure_non_negative(f"{name}[{index}].{field}", value)
        return value
    @staticmethod
    def _reject_domain_network_raw_address(name: str, value: str) -> None:
        if "@" in value or value.lower().startswith("mailto:"):
            raise DoxaBaseError(
                f"{name} looks like an individual address, not an aggregate "
                "domain or classification bucket"
            )
    @staticmethod
    def _ensure_positive_int(name: str, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise DoxaBaseError(f"{name} must be a positive integer")
    def _profile_bundle_handoff_entrypoints(
        self,
        *,
        dataset_iri: str,
        shared_evidence_iri: str | None,
        dataset_profile: DatasetProfileRecord,
        column_profiles: list[ColumnProfileRecord],
    ) -> ProfileBundleHandoffEntryPoints:
        dataset_profile_observation_iri = (
            dataset_profile.observation.observation_iri
        )
        column_profile_observation_iris = [
            column_profile.observation.observation_iri
            for column_profile in column_profiles
        ]
        profile_observation_iris = [
            dataset_profile_observation_iri,
            *column_profile_observation_iris,
        ]
        profile_run_evidence_iri = (
            dataset_profile.observation.evidence_iri
            if shared_evidence_iri is not None
            else None
        )
        dataset_describe_available = self._subject_exists(
            dataset_iri,
            self._expand_graphs(["map"]),
        )
        map_dataset_recorded = dataset_profile.map_dataset is not None
        profile_run_available = profile_run_evidence_iri is not None
        map_graphs = self._expand_graphs(["map"])
        updated_map_column_iris = [
            column_profile.column_iri
            for column_profile in column_profiles
            if column_profile.map_column is not None
        ]
        mapped_profiled_column_iris = [
            column_profile.column_iri
            for column_profile in column_profiles
            if self.expand_iri("rc:Column")
            in self._types_from_graphs(map_graphs, column_profile.column_iri)
        ]
        suggested_next_actions: list[SuggestedNextAction] = []

        def add_action(
            tool_name: str,
            arguments: dict[str, Any],
            reason: str,
            *,
            action_label: str,
            call: str,
        ) -> None:
            suggested_next_actions.append(
                SuggestedNextAction(
                    action_label=action_label,
                    tool_name=tool_name,
                    mcp_tool_name=f"doxabase.{tool_name}",
                    arguments=arguments,
                    reason=reason,
                    call=call,
                )
            )

        if dataset_describe_available:
            add_action(
                "describe_dataset",
                {"iri": dataset_iri},
                (
                    "Inspect the bounded dataset view with current map facts "
                    "and returned profile summaries."
                ),
                action_label="Describe dataset",
                call=f"describe_dataset({dataset_iri!r})",
            )
        if profile_run_available:
            add_action(
                "describe_profile_run",
                {
                    "dataset_iri": dataset_iri,
                    "evidence_iri": profile_run_evidence_iri,
                },
                (
                    "Inspect every returned profile observation linked to the "
                    "shared evidence run."
                ),
                action_label="Describe profile run",
                call=(
                    "describe_profile_run("
                    f"{dataset_iri!r}, {profile_run_evidence_iri!r}"
                    ")"
                ),
            )
        if dataset_describe_available and profile_run_available:
            add_action(
                "draft_profile_map_updates",
                {
                    "dataset_iri": dataset_iri,
                    "evidence_iri": profile_run_evidence_iri,
                },
                (
                    "Draft reviewable map update recommendations from this "
                    "profile run before deciding which findings should become "
                    "durable map facts."
                ),
                action_label="Draft profile map updates",
                call=(
                    "draft_profile_map_updates("
                    f"{dataset_iri!r}, {profile_run_evidence_iri!r}"
                    ")"
                ),
            )
        if dataset_describe_available:
            add_action(
                "describe_context_slice",
                {"seed_iris": [dataset_iri], "profile": "dataset_brief"},
                (
                    "Load route-explained dataset context before deciding "
                    "which profile findings should become durable map facts."
                ),
                action_label="Load dataset context slice",
                call=(
                    "describe_context_slice("
                    f"[{dataset_iri!r}], profile='dataset_brief'"
                    ")"
                ),
            )
        add_action(
            "describe_context_slice",
            {"seed_iris": profile_observation_iris, "profile": "dataset_brief"},
            (
                "Load profile-observation-seeded context when map dataset "
                "context is unavailable or the profile run needs a direct handoff."
            ),
            action_label="Load profile context slice",
            call=(
                "describe_context_slice("
                f"{profile_observation_iris!r}, profile='dataset_brief'"
                ")"
            ),
        )
        suggested_next_calls = [action.call for action in suggested_next_actions]
        if dataset_describe_available and profile_run_available:
            if map_dataset_recorded:
                handoff_note = (
                    "Map dataset context is available; use describe_dataset for the "
                    "bounded dataset view or describe_profile_run for the shared "
                    "evidence run."
                )
            else:
                handoff_note = (
                    "Map dataset context already existed; this profile bundle did "
                    "not write dataset map facts or a row-count snapshot. Use "
                    "describe_dataset for the bounded dataset view or "
                    "describe_profile_run for the shared evidence run."
                )
        elif dataset_describe_available:
            if map_dataset_recorded:
                handoff_note = (
                    "Map dataset context is available, but no shared evidence IRI "
                    "was supplied; use profile_observation_iris for run-level "
                    "handoff."
                )
            else:
                handoff_note = (
                    "Map dataset context already existed, but this profile bundle "
                    "did not write dataset map facts and no shared evidence IRI "
                    "was supplied; use profile_observation_iris for run-level "
                    "handoff."
                )
        elif profile_run_available:
            handoff_note = (
                "No map dataset subject is currently available; use "
                "describe_profile_run or seed describe_context_slice from the "
                "profile observation IRIs."
            )
        else:
            handoff_note = (
                "No map dataset subject or shared evidence IRI is currently "
                "available; use profile_observation_iris as the handoff seeds."
            )
        return ProfileBundleHandoffEntryPoints(
            dataset_iri=dataset_iri,
            shared_evidence_iri=profile_run_evidence_iri,
            dataset_profile_observation_iri=dataset_profile_observation_iri,
            column_profile_observation_iris=column_profile_observation_iris,
            profile_observation_iris=profile_observation_iris,
            map_dataset_recorded=map_dataset_recorded,
            map_column_iris=updated_map_column_iris,
            updated_map_column_iris=updated_map_column_iris,
            mapped_profiled_column_iris=mapped_profiled_column_iris,
            dataset_describe_available=dataset_describe_available,
            profile_run_available=profile_run_available,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=suggested_next_calls,
            handoff_note=handoff_note,
        )
    def _preflight_profile_bundle_evidence_summaries(
        self,
        *,
        shared_evidence_iri: str | None,
        dataset_evidence_summary: str | None,
        column_profiles: Iterable[Mapping[str, Any]],
    ) -> None:
        summaries_by_evidence: dict[str, tuple[str, str]] = {}

        def add_summary(
            label: str,
            evidence_iri: Any,
            evidence_summary: Any,
        ) -> None:
            if not isinstance(evidence_iri, str) or not evidence_iri.strip():
                return
            if not isinstance(evidence_summary, str) or not evidence_summary.strip():
                return
            evidence_value = evidence_iri.strip()
            existing = summaries_by_evidence.get(evidence_value)
            if existing is not None and existing[0] != evidence_summary:
                raise DoxaBaseError(
                    "record_profile_bundle reuses evidence_iri "
                    f"{evidence_value!r} with conflicting evidence_summary "
                    f"values in {existing[1]} and {label}"
                )
            summaries_by_evidence[evidence_value] = (evidence_summary, label)
            self._preflight_evidence_summary_reuse(
                evidence_value,
                evidence_summary,
                field_name=f"{label}.evidence_summary",
            )

        add_summary(
            "dataset profile",
            shared_evidence_iri,
            dataset_evidence_summary,
        )
        for index, column_kwargs in enumerate(column_profiles):
            add_summary(
                f"column_profiles[{index}]",
                column_kwargs.get("evidence_iri"),
                column_kwargs.get("evidence_summary"),
            )
    def _profile_bundle_pattern_support_scope(self, value: str | None) -> str:
        if value is None:
            return "dataset_profile"
        scope = value.strip().lower()
        if scope in {"dataset_profile", "all_profiles"}:
            return scope
        raise DoxaBaseError(
            "pattern_support_scope must be one of: dataset_profile, all_profiles"
        )
    def _preflight_profile_bundle_column(
        self,
        index: int,
        column_kwargs: Mapping[str, Any],
    ) -> None:
        column_value = self._required_iri(
            f"column_profiles[{index}].column_iri",
            column_kwargs["column_iri"],
        )
        table_value = (
            self._required_iri(
                f"column_profiles[{index}].table_iri",
                column_kwargs["table_iri"],
            )
            if column_kwargs.get("table_iri") is not None
            else None
        )
        column_name = column_kwargs["column_name"]
        column_name_value = column_name.strip()
        if not column_name_value:
            raise DoxaBaseError(
                f"column_profiles[{index}].column_name must not be empty"
            )
        summary = column_kwargs["summary"]
        if not summary.strip():
            raise DoxaBaseError(
                f"column_profiles[{index}].summary must not be empty"
            )
        for name in (
            "sample_size",
            "row_count",
            "null_count",
            "distinct_count",
        ):
            self._ensure_non_negative(
                f"column_profiles[{index}].{name}",
                column_kwargs.get(name),
            )
        self._profile_value_frequency_values(
            column_kwargs.get("value_frequencies"),
            field_name=f"column_profiles[{index}].value_frequencies",
        )
        self._profile_metric_values(
            column_kwargs.get("profile_metrics"),
            field_name=f"column_profiles[{index}].profile_metrics",
        )

        evidence_sources = column_kwargs.get("evidence_sources")
        if isinstance(evidence_sources, str):
            evidence_source_values = [evidence_sources]
        else:
            evidence_source_values = list(evidence_sources or [])
        if any(not isinstance(source, str) for source in evidence_source_values):
            raise DoxaBaseError(
                f"column_profiles[{index}].evidence_sources must contain strings"
            )
        if column_kwargs.get("physical_type") is not None:
            self._resource_ref(
                f"column_profiles[{index}].physical_type",
                column_kwargs["physical_type"],
            )
        if column_kwargs.get("value_type") is not None:
            self._resource_ref(
                f"column_profiles[{index}].value_type",
                column_kwargs["value_type"],
            )

        should_update_map = column_kwargs.get("update_map_column", True) and (
            table_value is not None
            or column_kwargs.get("map_label") is not None
            or column_kwargs.get("map_description") is not None
            or column_kwargs.get("physical_type") is not None
            or column_kwargs.get("value_type") is not None
            or column_kwargs.get("nullable") is not None
        )
        if should_update_map:
            if table_value is not None:
                self._resource_ref(
                    f"column_profiles[{index}].table_iri",
                    table_value,
                )

        if self._profile_pattern_requested(
            column_kwargs.get("pattern_summary"),
            column_kwargs.get("pattern_text"),
            column_kwargs.get("pattern_rationale"),
        ):
            self._preflight_profile_pattern(
                primary_resource_iri=column_value,
                pattern_map_implications=column_kwargs.get(
                    "pattern_map_implications"
                ),
                profile_metric_sets=(
                    (
                        f"column_profiles[{index}].profile_metrics",
                        column_kwargs.get("profile_metrics"),
                    ),
                ),
                profile_value_type_fields=(
                    (
                        f"column_profiles[{index}].value_type",
                        column_kwargs.get("value_type"),
                    ),
                ),
                pattern_confidence=column_kwargs.get("pattern_confidence"),
                pattern_status=column_kwargs.get("pattern_status"),
                pattern_stability=column_kwargs.get("pattern_stability"),
            )
    def record_profiled_parquet_table(
        self,
        iri: str,
        *,
        dataset_summary: str,
        evidence_summary: str,
        columns: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None = None,
        label: str | None = None,
        description: str | None = None,
        path_templates: Iterable[str] | str | None = None,
        row_count: int | None = None,
        sample_size: int | None = None,
        sample_scope: str | None = None,
        sample_method: str | None = None,
        observed_at: datetime | str | None = None,
        observed_by: str | None = None,
        evidence_sources: Iterable[str] | str | None = None,
        shared_evidence_iri: str | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
        value_frequencies: Iterable[Mapping[str, Any]] | None = None,
        profile_metrics: Iterable[Mapping[str, Any]] | None = None,
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
        compression_codec: str | None = None,
        physical_layout_verification_status: str | None = None,
        physical_layout_verification_note: str | None = None,
        pattern_summary: str | None = None,
        pattern_text: str | None = None,
        pattern_rationale: str | None = None,
        pattern_confidence: str | None = "rc:MediumConfidence",
        pattern_status: str | None = "rc:Tentative",
        pattern_stability: str | None = "rc:EmergingPattern",
        pattern_map_implications: Iterable[str] | str | None = None,
        pattern_support_scope: TypingLiteral["dataset_profile", "all_profiles"]
        | str = "all_profiles",
    ) -> ProfiledParquetTableRecord:
        dataset_iri = self._required_iri("iri", iri)
        if not isinstance(dataset_summary, str) or not dataset_summary.strip():
            raise DoxaBaseError("dataset_summary must be a non-empty string")
        if not isinstance(evidence_summary, str) or not evidence_summary.strip():
            raise DoxaBaseError("evidence_summary must be a non-empty string")
        self._ensure_non_negative("row_count", row_count)
        self._ensure_non_negative("sample_size", sample_size)
        self._ensure_non_negative("null_count", null_count)
        self._ensure_non_negative("distinct_count", distinct_count)
        if observed_at is not None:
            self._datetime_literal(observed_at, name="observed_at")
        for name, value in (
            ("sample_scope", sample_scope),
            ("sample_method", sample_method),
            ("observed_by", observed_by),
        ):
            self._preflight_optional_string(name, value)
        value_frequency_items = (
            list(value_frequencies) if value_frequencies is not None else None
        )
        profile_metric_items = (
            list(profile_metrics) if profile_metrics is not None else None
        )
        self._profile_value_frequency_values(
            value_frequency_items,
            field_name="value_frequencies",
        )
        self._profile_metric_values(
            profile_metric_items,
            field_name="profile_metrics",
        )
        profile_sample_size = sample_size if sample_size is not None else row_count
        profile_sample_scope = sample_scope
        profile_sample_method = sample_method or (
            "Caller-supplied reviewed Parquet metadata/profile; DoxaBase did no I/O."
        )
        evidence_value = (
            str(self._resource_ref("shared_evidence_iri", shared_evidence_iri))
            if shared_evidence_iri is not None
            else f"{dataset_iri}/profile-evidence/parquet"
        )
        map_columns, profile_columns = self._normalise_profiled_parquet_columns(
            dataset_iri=dataset_iri,
            columns=columns,
            row_count=row_count,
            sample_size=profile_sample_size,
            sample_scope=profile_sample_scope,
            sample_method=profile_sample_method,
            observed_at=observed_at,
            observed_by=observed_by,
        )

        self._preflight_map_table_bundle(
            label=label,
            description=description,
            path_templates=path_templates,
            row_count_snapshot=row_count,
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
            file_format="rc:Parquet",
            compression_codec=compression_codec,
            physical_layout_verification_status=physical_layout_verification_status,
            physical_layout_verification_note=physical_layout_verification_note,
        )
        self._preflight_profiled_parquet_profile_bundle(
            dataset_iri=dataset_iri,
            dataset_summary=dataset_summary,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            shared_evidence_iri=evidence_value,
            sample_size=profile_sample_size,
            row_count=row_count,
            null_count=null_count,
            distinct_count=distinct_count,
            value_frequencies=value_frequency_items,
            profile_metrics=profile_metric_items,
            column_profiles=profile_columns,
            pattern_summary=pattern_summary,
            pattern_text=pattern_text,
            pattern_rationale=pattern_rationale,
            pattern_confidence=pattern_confidence,
            pattern_status=pattern_status,
            pattern_stability=pattern_stability,
            pattern_map_implications=pattern_map_implications,
            pattern_support_scope=pattern_support_scope,
        )

        table_bundle = self.record_map_table_bundle(
            dataset_iri,
            label=label,
            description=description,
            columns=map_columns,
            path_templates=path_templates,
            row_count_snapshot=row_count,
            row_semantics=row_semantics,
            entity_key=entity_key,
            schema_stability=schema_stability,
            layout_verification_status=layout_verification_status,
            layout_verification_note=layout_verification_note,
            caveats=caveats,
            companion_datasets=companion_datasets,
            extra_types=extra_types,
            storage_access_iri=storage_access_iri,
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
            physical_layout_iri=physical_layout_iri,
            physical_layout_label=physical_layout_label,
            physical_layout_description=physical_layout_description,
            file_format="rc:Parquet",
            compression_codec=compression_codec,
            physical_layout_verification_status=physical_layout_verification_status,
            physical_layout_verification_note=physical_layout_verification_note,
        )
        profile_bundle = self.record_profile_bundle(
            dataset_iri,
            dataset_summary=dataset_summary,
            column_profiles=profile_columns,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            sample_size=profile_sample_size,
            sample_scope=profile_sample_scope,
            sample_method=profile_sample_method,
            row_count=row_count,
            null_count=null_count,
            distinct_count=distinct_count,
            value_frequencies=value_frequency_items,
            profile_metrics=profile_metric_items,
            update_map_snapshot=False,
            pattern_summary=pattern_summary,
            pattern_text=pattern_text,
            pattern_rationale=pattern_rationale,
            pattern_confidence=pattern_confidence,
            pattern_status=pattern_status,
            pattern_stability=pattern_stability,
            pattern_map_implications=pattern_map_implications,
            pattern_support_scope=pattern_support_scope,
            shared_evidence_iri=evidence_value,
            column_defaults={"update_map_column": False},
        )
        profile_draft = self.draft_profile_map_updates(dataset_iri, evidence_value)
        query_context = self.describe_query_context(dataset_iri)
        suggested_next_actions = self._profiled_table_suggested_next_actions(
            table_bundle.suggested_next_actions,
            profile_bundle.handoff_entrypoints.suggested_next_actions,
        )
        return ProfiledParquetTableRecord(
            dataset_iri=dataset_iri,
            shared_evidence_iri=evidence_value,
            table_bundle=table_bundle,
            profile_bundle=profile_bundle,
            profile_observation_count=len(
                profile_bundle.handoff_entrypoints.profile_observation_iris
            ),
            profile_draft_recommendation_count=profile_draft.recommendation_count,
            query_readiness=query_context.readiness,
            query_issue_codes=[issue.code for issue in query_context.issues],
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[action.call for action in suggested_next_actions],
        )
    def record_profile_to_capsule_manifest(
        self,
        manifest: Mapping[str, Any],
    ) -> ProfileToCapsuleManifestRecord:
        if self.read_only:
            raise DoxaBaseError(
                "record_profile_to_capsule_manifest requires a writable capsule; "
                "open read-only capsules with DoxaBase.open_readonly(path) for "
                "inspection only"
            )
        manifest_spec = self._normalise_profile_to_capsule_manifest(manifest)
        with self._preflight_clone() as clone:
            clone._apply_profile_to_capsule_manifest(manifest_spec)
            validation = clone.validate_graph(scope="all")
            if not validation.conforms:
                raise DoxaBaseError(
                    "record_profile_to_capsule_manifest would make the capsule "
                    "invalid: "
                    + self._validation_failure_summary(validation)
                )
        return self._apply_profile_to_capsule_manifest(manifest_spec)
    def _apply_profile_to_capsule_manifest(
        self,
        manifest_spec: Mapping[str, Any],
    ) -> ProfileToCapsuleManifestRecord:
        caveat_records = [
            self.record_map_caveat(**caveat_spec)
            for caveat_spec in manifest_spec["caveats"]
        ]
        table_records = [
            self.record_profiled_parquet_table(**table_spec)
            for table_spec in manifest_spec["tables"]
        ]
        analysis_view_bundle = (
            self.record_map_analysis_view_bundle(manifest_spec["analysis_views"])
            if manifest_spec["analysis_views"]
            else None
        )
        domain_network_profile_records = [
            self.record_domain_network_profile(**profile_spec)
            for profile_spec in manifest_spec["domain_network_profiles"]
        ]
        query_readiness_counts: dict[str, int] = {}
        query_issue_code_counts: dict[str, int] = {}
        for table_record in table_records:
            query_readiness_counts[table_record.query_readiness] = (
                query_readiness_counts.get(table_record.query_readiness, 0) + 1
            )
            for issue_code in table_record.query_issue_codes:
                query_issue_code_counts[issue_code] = (
                    query_issue_code_counts.get(issue_code, 0) + 1
                )
        suggested_next_actions = self._dedupe_suggested_next_actions(
            [
                *(
                    action
                    for table_record in table_records
                    for action in table_record.suggested_next_actions
                ),
                *(
                    analysis_view_bundle.suggested_next_actions
                    if analysis_view_bundle is not None
                    else []
                ),
                *(
                    action
                    for profile_record in domain_network_profile_records
                    for action in profile_record.suggested_next_actions
                ),
            ]
        )
        domain_network_caveat_records = [
            record.caveat
            for record in domain_network_profile_records
            if record.caveat is not None
        ]
        domain_network_analysis_view_iris = [
            record.analysis_view.iri
            for record in domain_network_profile_records
            if record.analysis_view is not None
        ]
        domain_network_profile_evidence_iris = [
            record.evidence_iri
            for record in domain_network_profile_records
            if record.evidence_iri is not None
        ]
        domain_network_pattern_iris = [
            record.pattern.pattern_iri
            for record in domain_network_profile_records
            if record.pattern is not None
        ]
        table_profile_observation_count = sum(
            record.profile_observation_count for record in table_records
        )
        domain_network_profile_observation_count = sum(
            len(record.profile_observation_iris)
            for record in domain_network_profile_records
        )
        analysis_view_iris = list(
            dict.fromkeys(
                [
                    *(
                        analysis_view_bundle.view_iris
                        if analysis_view_bundle is not None
                        else []
                    ),
                    *domain_network_analysis_view_iris,
                ]
            )
        )
        all_caveat_records = [*caveat_records, *domain_network_caveat_records]
        caveat_iris = list(dict.fromkeys(record.iri for record in all_caveat_records))
        return ProfileToCapsuleManifestRecord(
            manifest_format=manifest_spec["format"],
            caveat_records=all_caveat_records,
            table_records=table_records,
            analysis_view_bundle=analysis_view_bundle,
            domain_network_profile_records=domain_network_profile_records,
            caveat_iris=caveat_iris,
            table_iris=[record.dataset_iri for record in table_records],
            shared_evidence_iris=[
                record.shared_evidence_iri for record in table_records
            ],
            analysis_view_iris=analysis_view_iris,
            domain_network_profile_evidence_iris=domain_network_profile_evidence_iris,
            domain_network_pattern_iris=domain_network_pattern_iris,
            caveat_count=len(caveat_iris),
            table_count=len(table_records),
            analysis_view_count=len(analysis_view_iris),
            domain_network_profile_count=len(domain_network_profile_records),
            domain_network_profile_observation_count=(
                domain_network_profile_observation_count
            ),
            profile_observation_count=(
                table_profile_observation_count
                + domain_network_profile_observation_count
            ),
            query_readiness_counts=query_readiness_counts,
            query_issue_code_counts=query_issue_code_counts,
            suggested_next_actions=suggested_next_actions,
            suggested_next_calls=[action.call for action in suggested_next_actions],
        )
    def _normalise_profile_to_capsule_manifest(
        self,
        manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(manifest, MappingABC):
            raise DoxaBaseError("manifest must be an object")
        allowed_fields = {
            "format",
            "table_defaults",
            "caveats",
            "tables",
            "analysis_views",
            "domain_network_profiles",
        }
        unknown_fields = sorted(set(manifest) - allowed_fields)
        if unknown_fields:
            raise DoxaBaseError(
                "manifest has unsupported field(s): " + ", ".join(unknown_fields)
            )
        manifest_format = manifest.get("format")
        if manifest_format != PROFILE_TO_CAPSULE_MANIFEST_FORMAT:
            raise DoxaBaseError(
                "manifest format must be "
                f"{PROFILE_TO_CAPSULE_MANIFEST_FORMAT!r}"
            )
        table_defaults_value = manifest.get("table_defaults")
        if table_defaults_value is None:
            table_defaults: Mapping[str, Any] = {}
        elif isinstance(table_defaults_value, MappingABC):
            table_defaults = table_defaults_value
        else:
            raise DoxaBaseError("table_defaults must be an object")
        caveat_specs = self._normalise_profile_manifest_caveats(
            manifest.get("caveats"),
        )
        table_specs = self._normalise_profile_manifest_tables(
            manifest.get("tables"),
            table_defaults=table_defaults,
        )
        analysis_view_values = self._normalise_manifest_object_list(
            "analysis_views",
            manifest.get("analysis_views"),
        )
        analysis_view_specs = (
            self._normalise_analysis_view_bundle_specs(analysis_view_values)
            if analysis_view_values
            else []
        )
        domain_network_profile_specs = (
            self._normalise_profile_manifest_domain_network_profiles(
                manifest.get("domain_network_profiles"),
            )
        )
        used_iris = {spec["iri"] for spec in table_specs}
        for index, caveat_spec in enumerate(caveat_specs, start=1):
            caveat_iri = caveat_spec["iri"]
            if caveat_iri in used_iris:
                raise DoxaBaseError(
                    f"caveats[{index}].iri duplicates another manifest resource: "
                    f"{caveat_iri}"
                )
            used_iris.add(caveat_iri)
        for view_spec in analysis_view_specs:
            view_iri = view_spec["iri"]
            if view_iri in used_iris:
                raise DoxaBaseError(
                    f"analysis view IRI duplicates another manifest resource: {view_iri}"
                )
            used_iris.add(view_iri)
        for index, profile_spec in enumerate(domain_network_profile_specs, start=1):
            for field, iri_value in self._profile_manifest_domain_network_created_iris(
                profile_spec,
            ):
                if iri_value in used_iris:
                    raise DoxaBaseError(
                        f"domain_network_profiles[{index}].{field} duplicates "
                        f"another manifest resource: {iri_value}"
                    )
                used_iris.add(iri_value)
        return {
            "format": manifest_format,
            "caveats": caveat_specs,
            "tables": table_specs,
            "analysis_views": analysis_view_specs,
            "domain_network_profiles": domain_network_profile_specs,
        }
    def _normalise_profiled_parquet_columns(
        self,
        *,
        dataset_iri: str,
        columns: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        row_count: int | None,
        sample_size: int | None,
        sample_scope: str | None,
        sample_method: str | None,
        observed_at: datetime | str | None,
        observed_by: str | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
            "summary",
            "row_count",
            "null_count",
            "distinct_count",
            "value_frequencies",
            "profile_metrics",
            "sample_size",
            "sample_scope",
            "sample_method",
            "observed_at",
            "observed_by",
            "pattern_summary",
            "pattern_text",
            "pattern_rationale",
            "pattern_confidence",
            "pattern_status",
            "pattern_stability",
            "pattern_map_implications",
            "observation_iri",
            "pattern_iri",
        }
        map_columns: list[dict[str, Any]] = []
        profile_columns: list[dict[str, Any]] = []
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
            column_name_value = column_name.strip()
            column_iri_value = item.get("column_iri", item.get("iri"))
            if column_iri_value is None:
                column_iri = self._default_table_bundle_column_iri(
                    dataset_iri,
                    column_name_value,
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
            nullable = item.get("nullable")
            if nullable is not None and not isinstance(nullable, bool):
                raise DoxaBaseError(f"columns[{index}].nullable must be a boolean")
            if physical_type is not None:
                self._resource_ref(f"columns[{index}].physical_type", physical_type)
            if value_type is not None:
                self._resource_ref(f"columns[{index}].value_type", value_type)
            observed_at_value = item.get("observed_at", observed_at)
            if observed_at_value is not None:
                self._datetime_literal(
                    observed_at_value,
                    name=f"columns[{index}].observed_at",
                )
            observed_by_value = optional_string("observed_by") or observed_by
            sample_scope_value = optional_string("sample_scope") or sample_scope
            sample_method_value = optional_string("sample_method") or sample_method
            observation_iri = optional_string("observation_iri")
            pattern_iri = optional_string("pattern_iri")
            if observation_iri is not None:
                self._resource_ref(f"columns[{index}].observation_iri", observation_iri)
            if pattern_iri is not None:
                self._resource_ref(f"columns[{index}].pattern_iri", pattern_iri)

            map_columns.append(
                {
                    "column_iri": column_iri,
                    "column_name": column_name_value,
                    "label": optional_string("label"),
                    "description": optional_string("description"),
                    "physical_type": physical_type,
                    "value_type": value_type,
                    "nullable": nullable,
                }
            )
            value_frequencies = item.get("value_frequencies")
            profile_metrics = item.get("profile_metrics")
            profile_column = {
                "column_iri": column_iri,
                "column_name": column_name_value,
                "summary": optional_string("summary")
                or (
                    f"{column_name_value} profile captured from reviewed "
                    "Parquet metadata."
                ),
                "table_iri": dataset_iri,
                "observed_at": observed_at_value,
                "observed_by": observed_by_value,
                "sample_size": item.get("sample_size", sample_size),
                "sample_scope": sample_scope_value,
                "sample_method": sample_method_value,
                "row_count": item.get("row_count", row_count),
                "null_count": item.get("null_count"),
                "distinct_count": item.get("distinct_count"),
                "value_frequencies": (
                    list(value_frequencies)
                    if value_frequencies is not None
                    else None
                ),
                "profile_metrics": (
                    list(profile_metrics) if profile_metrics is not None else None
                ),
                "update_map_column": False,
                "physical_type": physical_type,
                "value_type": value_type,
                "pattern_summary": optional_string("pattern_summary"),
                "pattern_text": optional_string("pattern_text"),
                "pattern_rationale": optional_string("pattern_rationale"),
                "pattern_confidence": item.get(
                    "pattern_confidence",
                    "rc:MediumConfidence",
                ),
                "pattern_status": item.get("pattern_status", "rc:Tentative"),
                "pattern_stability": item.get(
                    "pattern_stability",
                    "rc:EmergingPattern",
                ),
                "pattern_map_implications": item.get("pattern_map_implications"),
                "observation_iri": observation_iri,
                "pattern_iri": pattern_iri,
            }
            profile_columns.append(
                {key: value for key, value in profile_column.items() if value is not None}
            )
        return map_columns, profile_columns
    def _preflight_profiled_parquet_profile_bundle(
        self,
        *,
        dataset_iri: str,
        dataset_summary: str,
        evidence_summary: str,
        evidence_sources: Iterable[str] | str | None,
        shared_evidence_iri: str,
        sample_size: int | None,
        row_count: int | None,
        null_count: int | None,
        distinct_count: int | None,
        value_frequencies: Iterable[Mapping[str, Any]] | None,
        profile_metrics: Iterable[Mapping[str, Any]] | None,
        column_profiles: list[dict[str, Any]],
        pattern_summary: str | None,
        pattern_text: str | None,
        pattern_rationale: str | None,
        pattern_confidence: str | None,
        pattern_status: str | None,
        pattern_stability: str | None,
        pattern_map_implications: Iterable[str] | str | None,
        pattern_support_scope: str,
    ) -> None:
        if not dataset_summary.strip():
            raise DoxaBaseError("dataset_summary must not be empty")
        if not evidence_summary.strip():
            raise DoxaBaseError("evidence_summary must not be empty")
        if isinstance(evidence_sources, str):
            evidence_source_values = [evidence_sources]
        else:
            evidence_source_values = list(evidence_sources or [])
        if any(not isinstance(source, str) for source in evidence_source_values):
            raise DoxaBaseError("evidence_sources must contain strings")
        for name, value in (
            ("sample_size", sample_size),
            ("row_count", row_count),
            ("null_count", null_count),
            ("distinct_count", distinct_count),
        ):
            self._ensure_non_negative(name, value)
        self._profile_value_frequency_values(value_frequencies)
        self._profile_metric_values(profile_metrics)
        pattern_support_scope_value = self._profile_bundle_pattern_support_scope(
            pattern_support_scope
        )
        should_record_pattern = self._profile_pattern_requested(
            pattern_summary,
            pattern_text,
            pattern_rationale,
        )
        for index, column_kwargs in enumerate(column_profiles):
            self._preflight_profile_bundle_column(index, column_kwargs)
        self._preflight_profile_bundle_evidence_summaries(
            shared_evidence_iri=shared_evidence_iri,
            dataset_evidence_summary=evidence_summary,
            column_profiles=column_profiles,
        )
        if should_record_pattern:
            metric_sets: list[tuple[str, Iterable[Mapping[str, Any]] | None]] = [
                ("profile_metrics", profile_metrics)
            ]
            value_type_fields: list[tuple[str, str | None]] = []
            if pattern_support_scope_value == "all_profiles":
                metric_sets.extend(
                    (
                        f"columns[{index}].profile_metrics",
                        column_kwargs.get("profile_metrics"),
                    )
                    for index, column_kwargs in enumerate(column_profiles, start=1)
                )
                value_type_fields.extend(
                    (
                        f"columns[{index}].value_type",
                        column_kwargs.get("value_type"),
                    )
                    for index, column_kwargs in enumerate(column_profiles, start=1)
                )
            self._preflight_profile_pattern(
                primary_resource_iri=dataset_iri,
                pattern_map_implications=pattern_map_implications,
                profile_metric_sets=metric_sets,
                profile_value_type_fields=value_type_fields,
                pattern_confidence=pattern_confidence,
                pattern_status=pattern_status,
                pattern_stability=pattern_stability,
            )
    def _ensure_non_negative(self, name: str, value: int | None) -> None:
        if value is not None and value < 0:
            raise DoxaBaseError(f"{name} must be non-negative")
