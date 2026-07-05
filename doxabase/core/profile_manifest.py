"""Profile-to-capsule manifest normalisation and domain network profiles.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via ProfileManifestMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class ProfileManifestMixin:
    def _record_optional_domain_network_profile(
        self,
        dataset_iri: str,
        *,
        summary: str,
        observed_at: datetime | str | None,
        observed_by: str | None,
        evidence_summary: str,
        evidence_sources: Iterable[str] | str | None,
        evidence_iri: str,
        sample_size: int,
        sample_scope: str,
        sample_method: str,
        value_frequencies: list[dict[str, Any]],
    ) -> DatasetProfileRecord | None:
        if not value_frequencies:
            return None
        return self.record_dataset_profile(
            dataset_iri,
            summary=summary,
            observed_at=observed_at,
            observed_by=observed_by,
            evidence_summary=evidence_summary,
            evidence_sources=evidence_sources,
            evidence_iri=evidence_iri,
            sample_size=sample_size,
            sample_scope=sample_scope,
            sample_method=sample_method,
            value_frequencies=value_frequencies,
            update_map_snapshot=False,
        )
    def _normalise_profile_manifest_domain_network_profiles(
        self,
        profiles: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        profile_values = self._normalise_manifest_object_list(
            "domain_network_profiles",
            profiles,
        )
        allowed_fields = {
            "dataset_iri",
            "summary",
            "evidence_summary",
            "sample_size",
            "sample_scope",
            "sample_method",
            "extraction_method",
            "coverage_counts",
            "observed_at",
            "observed_by",
            "evidence_sources",
            "evidence_iri",
            "coverage_counts_exhaustive",
            "domain_pair_counts",
            "sender_domain_counts",
            "recipient_domain_counts",
            "domain_pair_min_count",
            "allow_low_frequency_domain_pairs",
            "analysis_view_iri",
            "analysis_view_label",
            "analysis_view_description",
            "analysis_view_row_count_snapshot",
            "analysis_view_query_text",
            "analysis_view_query_language",
            "analysis_view_query_engine",
            "caveat_iri",
            "caveat_label",
            "caveat_description",
            "caveat_severity",
            "pattern_summary",
            "pattern_text",
            "pattern_rationale",
            "pattern_confidence",
            "pattern_status",
            "pattern_stability",
        }
        specs: list[dict[str, Any]] = []
        for index, item in enumerate(profile_values, start=1):
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"domain_network_profiles[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            spec = copy.deepcopy(dict(item))
            dataset_value = spec.get("dataset_iri")
            if not isinstance(dataset_value, str) or not dataset_value.strip():
                raise DoxaBaseError(
                    "domain_network_profiles"
                    f"[{index}].dataset_iri must be a non-empty IRI or CURIE string"
                )
            spec["dataset_iri"] = str(
                self._resource_ref(
                    f"domain_network_profiles[{index}].dataset_iri",
                    dataset_value,
                )
            )
            for field in ("evidence_iri", "analysis_view_iri", "caveat_iri"):
                value = spec.get(field)
                if value is not None:
                    if not isinstance(value, str) or not value.strip():
                        raise DoxaBaseError(
                            f"domain_network_profiles[{index}].{field} must be a "
                            "non-empty IRI or CURIE string"
                        )
                    spec[field] = str(
                        self._resource_ref(
                            f"domain_network_profiles[{index}].{field}",
                            value,
                        )
                    )
            specs.append(spec)
        return specs
    @staticmethod
    def _profile_manifest_domain_network_created_iris(
        spec: Mapping[str, Any],
    ) -> list[tuple[str, str]]:
        created: list[tuple[str, str]] = []
        caveat_requested = (
            spec.get("caveat_description") is not None
            or spec.get("caveat_iri") is not None
        )
        if caveat_requested:
            created.append(
                (
                    "caveat_iri",
                    str(
                        spec.get("caveat_iri")
                        or f"{spec['dataset_iri']}/domain-network-caveat"
                    ),
                )
            )
        analysis_view_requested = any(
            spec.get(field) is not None
            for field in (
                "analysis_view_iri",
                "analysis_view_label",
                "analysis_view_description",
                "analysis_view_row_count_snapshot",
                "analysis_view_query_text",
                "analysis_view_query_language",
                "analysis_view_query_engine",
            )
        )
        if analysis_view_requested:
            created.append(
                (
                    "analysis_view_iri",
                    str(
                        spec.get("analysis_view_iri")
                        or f"{spec['dataset_iri']}/domain-network-analysis-view"
                    ),
                )
            )
        return created
    def _normalise_profile_manifest_caveats(
        self,
        caveats: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        caveat_values = self._normalise_manifest_object_list(
            "caveats",
            caveats,
        )
        allowed_fields = {
            "iri",
            "label",
            "description",
            "impact",
            "severity",
            "targets",
        }
        specs: list[dict[str, Any]] = []
        seen_iris: set[str] = set()
        for index, item in enumerate(caveat_values, start=1):
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"caveats[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            iri_value = item.get("iri")
            if not isinstance(iri_value, str) or not iri_value.strip():
                raise DoxaBaseError(
                    f"caveats[{index}].iri must be a non-empty IRI or CURIE string"
                )
            caveat_iri = str(self._resource_ref(f"caveats[{index}].iri", iri_value))
            if caveat_iri in seen_iris:
                raise DoxaBaseError(f"caveats[{index}].iri duplicates {caveat_iri}")
            seen_iris.add(caveat_iri)
            spec = {field: copy.deepcopy(item[field]) for field in item}
            spec["iri"] = caveat_iri
            specs.append(spec)
        return specs
    def _normalise_profile_manifest_tables(
        self,
        tables: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        *,
        table_defaults: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        default_unknown_fields = sorted(
            set(table_defaults) - self._profile_manifest_table_fields()
        )
        if default_unknown_fields:
            raise DoxaBaseError(
                "table_defaults has unsupported field(s): "
                + ", ".join(default_unknown_fields)
            )
        default_identity_fields = (
            {"iri", "table_iri", "dataset_iri"} & set(table_defaults)
        )
        if default_identity_fields:
            raise DoxaBaseError(
                "table_defaults cannot include table identity field(s): "
                + ", ".join(sorted(default_identity_fields))
            )
        table_values = self._normalise_manifest_object_list(
            "tables",
            tables,
            required=True,
        )
        specs: list[dict[str, Any]] = []
        seen_iris: set[str] = set()
        allowed_fields = self._profile_manifest_table_fields()
        for index, item in enumerate(table_values, start=1):
            unknown_fields = sorted(set(item) - allowed_fields)
            if unknown_fields:
                raise DoxaBaseError(
                    f"tables[{index}] has unsupported field(s): "
                    + ", ".join(unknown_fields)
                )
            spec = copy.deepcopy(dict(table_defaults))
            spec.update(copy.deepcopy(dict(item)))
            table_iri = self._profile_manifest_table_iri(spec, index=index)
            if table_iri in seen_iris:
                raise DoxaBaseError(f"tables[{index}].iri duplicates {table_iri}")
            seen_iris.add(table_iri)
            spec.pop("table_iri", None)
            spec.pop("dataset_iri", None)
            spec["iri"] = table_iri
            specs.append(spec)
        return specs
    @staticmethod
    def _profile_manifest_table_fields() -> set[str]:
        return {
            "iri",
            "table_iri",
            "dataset_iri",
            "dataset_summary",
            "evidence_summary",
            "columns",
            "label",
            "description",
            "path_templates",
            "row_count",
            "sample_size",
            "sample_scope",
            "sample_method",
            "observed_at",
            "observed_by",
            "evidence_sources",
            "shared_evidence_iri",
            "null_count",
            "distinct_count",
            "value_frequencies",
            "profile_metrics",
            "row_semantics",
            "entity_key",
            "schema_stability",
            "layout_verification_status",
            "layout_verification_note",
            "caveats",
            "companion_datasets",
            "extra_types",
            "storage_access_iri",
            "storage_label",
            "storage_description",
            "route_roles",
            "storage_protocol",
            "access_mode",
            "location_kind",
            "storage_root",
            "endpoint_profile",
            "bucket_name",
            "key_prefix",
            "region",
            "path_style_access",
            "credential_reference",
            "storage_path_templates",
            "storage_layout_verification_status",
            "storage_layout_verification_note",
            "physical_layout_iri",
            "physical_layout_label",
            "physical_layout_description",
            "compression_codec",
            "physical_layout_verification_status",
            "physical_layout_verification_note",
            "pattern_summary",
            "pattern_text",
            "pattern_rationale",
            "pattern_confidence",
            "pattern_status",
            "pattern_stability",
            "pattern_map_implications",
            "pattern_support_scope",
        }
    def _profile_manifest_table_iri(
        self,
        spec: Mapping[str, Any],
        *,
        index: int,
    ) -> str:
        identity_fields = [
            field for field in ("iri", "table_iri", "dataset_iri") if field in spec
        ]
        if not identity_fields:
            raise DoxaBaseError(
                f"tables[{index}].iri must be a non-empty IRI or CURIE string"
            )
        expanded_values: list[str] = []
        for field in identity_fields:
            value = spec.get(field)
            if not isinstance(value, str) or not value.strip():
                raise DoxaBaseError(
                    f"tables[{index}].{field} must be a non-empty IRI or CURIE string"
                )
            expanded_values.append(
                str(self._resource_ref(f"tables[{index}].{field}", value))
            )
        unique_values = list(dict.fromkeys(expanded_values))
        if len(unique_values) > 1:
            raise DoxaBaseError(
                f"tables[{index}] identity fields disagree: "
                + ", ".join(unique_values)
            )
        return unique_values[0]
