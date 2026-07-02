from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from doxabase.core import DoxaBaseError, PROFILE_TO_CAPSULE_MANIFEST_FORMAT


PROFILE_FACTS_FORMAT = "doxabase.reviewed_profile_facts.v1"

_TOP_LEVEL_FIELDS = {"format", "tables"}
_TABLE_FIELDS = {
    "iri",
    "row_count",
    "sample_size",
    "sample_scope",
    "sample_method",
    "observed_at",
    "observed_by",
    "evidence_summary",
    "evidence_sources",
    "shared_evidence_iri",
    "layout_verification_status",
    "layout_verification_note",
    "storage_layout_verification_status",
    "storage_layout_verification_note",
    "physical_layout_verification_status",
    "physical_layout_verification_note",
    "columns",
}
_COLUMN_FIELDS = {
    "summary",
    "row_count",
    "sample_size",
    "sample_scope",
    "sample_method",
    "observed_at",
    "observed_by",
    "null_count",
    "distinct_count",
    "value_frequencies",
    "profile_metrics",
}


def merge_reviewed_profile_facts(
    scaffold: Mapping[str, Any],
    profile_facts: Mapping[str, Any],
    *,
    profile_facts_source: str | None = None,
    add_profile_caveat: bool = True,
) -> dict[str, Any]:
    """Merge reviewed aggregate profile facts into a profile manifest scaffold."""

    _ensure_mapping(scaffold, "scaffold")
    _ensure_mapping(profile_facts, "profile_facts")
    if scaffold.get("format") != PROFILE_TO_CAPSULE_MANIFEST_FORMAT:
        raise DoxaBaseError(
            "scaffold format must be "
            f"{PROFILE_TO_CAPSULE_MANIFEST_FORMAT!r}"
        )
    _reject_unknown_fields(profile_facts, _TOP_LEVEL_FIELDS, "profile_facts")
    if profile_facts.get("format") != PROFILE_FACTS_FORMAT:
        raise DoxaBaseError(
            f"profile_facts format must be {PROFILE_FACTS_FORMAT!r}"
        )
    facts_tables = _required_list(profile_facts, "tables", "profile_facts")
    manifest = copy.deepcopy(dict(scaffold))
    manifest_tables = _required_list(manifest, "tables", "scaffold")
    table_by_iri = _scaffold_table_index(manifest_tables)

    for index, table_facts in enumerate(facts_tables, start=1):
        table = _ensure_mapping(
            table_facts,
            f"profile_facts.tables[{index}]",
        )
        _reject_unknown_fields(
            table,
            _TABLE_FIELDS,
            f"profile_facts.tables[{index}]",
        )
        table_iri = _required_non_empty_string(
            table,
            "iri",
            f"profile_facts.tables[{index}]",
        )
        if table_iri not in table_by_iri:
            raise DoxaBaseError(
                f"profile_facts.tables[{index}].iri does not match a scaffold "
                f"table: {table_iri}"
            )
        scaffold_table = table_by_iri[table_iri]
        _merge_table_facts(
            scaffold_table,
            table,
            table_context=f"profile_facts.tables[{index}]",
            profile_facts_source=profile_facts_source,
        )
        _merge_column_facts(
            scaffold_table,
            table,
            table_context=f"profile_facts.tables[{index}]",
        )
        if add_profile_caveat:
            _add_profile_caveat(
                manifest,
                scaffold_table,
                table_iri=table_iri,
                profile_facts_source=profile_facts_source,
            )

    manifest["format"] = PROFILE_TO_CAPSULE_MANIFEST_FORMAT
    return manifest


def write_merged_profile_manifest(
    output_path: str | Path,
    *,
    scaffold_path: str | Path,
    profile_facts_path: str | Path,
    overwrite: bool = False,
    add_profile_caveat: bool = True,
) -> dict[str, Any]:
    """Read scaffold and profile-facts JSON files, write the merged manifest."""

    scaffold_file = Path(scaffold_path)
    profile_file = Path(profile_facts_path)
    scaffold = _read_json_file(scaffold_file, "scaffold")
    profile_facts = _read_json_file(profile_file, "profile facts")
    manifest = merge_reviewed_profile_facts(
        scaffold,
        profile_facts,
        profile_facts_source=str(profile_file),
        add_profile_caveat=add_profile_caveat,
    )
    destination = Path(output_path)
    if destination.exists() and not overwrite:
        raise DoxaBaseError(
            f"Output manifest already exists: {destination}. Pass overwrite=True "
            "or --overwrite to replace it."
        )
    if destination.parent != Path("."):
        destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def merge_summary(
    manifest: Mapping[str, Any],
    *,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    tables = manifest.get("tables", [])
    caveats = manifest.get("caveats", [])
    merged_columns = 0
    for table in tables if isinstance(tables, list) else []:
        if not isinstance(table, Mapping):
            continue
        for column in table.get("columns", []):
            if isinstance(column, Mapping) and any(
                field in column
                for field in (
                    "null_count",
                    "distinct_count",
                    "value_frequencies",
                    "profile_metrics",
                )
            ):
                merged_columns += 1
    payload: dict[str, Any] = {
        "manifest_format": manifest.get("format"),
        "table_count": len(tables) if isinstance(tables, list) else 0,
        "caveat_count": len(caveats) if isinstance(caveats, list) else 0,
        "merged_column_count": merged_columns,
        "next_step": (
            "python -m doxabase.profile_to_capsule --capsule capsule.sqlite "
            "--manifest "
            f"{output_path if output_path is not None else '<reviewed-manifest.json>'}"
        ),
    }
    if output_path is not None:
        payload["output_path"] = str(output_path)
    return payload


def _merge_table_facts(
    scaffold_table: dict[str, Any],
    table_facts: Mapping[str, Any],
    *,
    table_context: str,
    profile_facts_source: str | None,
) -> None:
    if "sample_scope" not in table_facts:
        raise DoxaBaseError(f"{table_context}.sample_scope is required")
    if "sample_method" not in table_facts:
        raise DoxaBaseError(f"{table_context}.sample_method is required")
    for field in ("sample_scope", "sample_method"):
        scaffold_table[field] = _required_non_empty_string(
            table_facts,
            field,
            table_context,
        )
    for field in ("observed_at", "observed_by", "evidence_summary"):
        if field in table_facts:
            scaffold_table[field] = _optional_non_empty_string(
                table_facts,
                field,
                table_context,
            )
    for field in (
        "layout_verification_status",
        "layout_verification_note",
        "storage_layout_verification_status",
        "storage_layout_verification_note",
        "physical_layout_verification_status",
        "physical_layout_verification_note",
    ):
        if field in table_facts:
            scaffold_table[field] = _optional_non_empty_string(
                table_facts,
                field,
                table_context,
            )
    if "shared_evidence_iri" in table_facts:
        scaffold_table["shared_evidence_iri"] = _optional_non_empty_string(
            table_facts,
            "shared_evidence_iri",
            table_context,
        )
    if "row_count" in table_facts:
        row_count = _non_negative_int(
            table_facts["row_count"],
            f"{table_context}.row_count",
        )
        existing = scaffold_table.get("row_count")
        if existing is not None and existing != row_count:
            raise DoxaBaseError(
                f"{table_context}.row_count={row_count} does not match "
                f"scaffold row_count={existing}"
            )
        scaffold_table["row_count"] = row_count
        scaffold_table["sample_size"] = _non_negative_int(
            table_facts.get("sample_size", row_count),
            f"{table_context}.sample_size",
        )
    elif "sample_size" in table_facts:
        scaffold_table["sample_size"] = _non_negative_int(
            table_facts["sample_size"],
            f"{table_context}.sample_size",
        )
    if "evidence_sources" in table_facts:
        sources = _string_list(
            table_facts["evidence_sources"],
            f"{table_context}.evidence_sources",
        )
        _append_unique_strings(scaffold_table, "evidence_sources", sources)
    if profile_facts_source is not None:
        _append_unique_strings(
            scaffold_table,
            "evidence_sources",
            [profile_facts_source],
        )
    if "evidence_summary" not in scaffold_table:
        scaffold_table["evidence_summary"] = (
            "Reviewed external aggregate profile facts merged into the Parquet "
            "manifest scaffold; DoxaBase did no raw-row ingestion."
        )


def _merge_column_facts(
    scaffold_table: dict[str, Any],
    table_facts: Mapping[str, Any],
    *,
    table_context: str,
) -> int:
    columns = table_facts.get("columns")
    if columns is None:
        raise DoxaBaseError(f"{table_context}.columns is required")
    if not isinstance(columns, Mapping):
        raise DoxaBaseError(f"{table_context}.columns must be an object")
    if not columns and "row_count" not in table_facts:
        raise DoxaBaseError(
            f"{table_context}.columns can be empty only when row_count is present"
        )
    scaffold_columns = scaffold_table.get("columns", [])
    if not isinstance(scaffold_columns, list):
        raise DoxaBaseError(
            f"scaffold table {scaffold_table.get('iri')} columns must be a list"
        )
    column_by_name: dict[str, dict[str, Any]] = {}
    for index, column in enumerate(scaffold_columns, start=1):
        if not isinstance(column, dict):
            raise DoxaBaseError(f"scaffold columns[{index}] must be an object")
        name = column.get("column_name")
        if not isinstance(name, str) or not name.strip():
            raise DoxaBaseError(f"scaffold columns[{index}].column_name is required")
        if name in column_by_name:
            raise DoxaBaseError(f"scaffold has duplicate column_name {name!r}")
        column_by_name[name] = column
    merged = 0
    for column_name, column_facts_value in columns.items():
        if not isinstance(column_name, str) or not column_name.strip():
            raise DoxaBaseError(f"{table_context}.columns keys must be column names")
        if column_name not in column_by_name:
            raise DoxaBaseError(
                f"{table_context}.columns.{column_name} does not match a "
                "scaffold column"
            )
        column_context = f"{table_context}.columns.{column_name}"
        column_facts = _ensure_mapping(column_facts_value, column_context)
        _reject_unknown_fields(column_facts, _COLUMN_FIELDS, column_context)
        _merge_one_column(column_by_name[column_name], column_facts, column_context)
        merged += 1
    return merged


def _merge_one_column(
    scaffold_column: dict[str, Any],
    column_facts: Mapping[str, Any],
    column_context: str,
) -> None:
    for field in (
        "summary",
        "sample_scope",
        "sample_method",
        "observed_at",
        "observed_by",
    ):
        if field in column_facts:
            scaffold_column[field] = _optional_non_empty_string(
                column_facts,
                field,
                column_context,
            )
    for field in ("row_count", "sample_size", "null_count", "distinct_count"):
        if field in column_facts:
            scaffold_column[field] = _non_negative_int(
                column_facts[field],
                f"{column_context}.{field}",
            )
    if "value_frequencies" in column_facts:
        scaffold_column["value_frequencies"] = _value_frequencies(
            column_facts["value_frequencies"],
            f"{column_context}.value_frequencies",
        )
    if "profile_metrics" in column_facts:
        scaffold_column["profile_metrics"] = _profile_metrics(
            column_facts["profile_metrics"],
            f"{column_context}.profile_metrics",
        )


def _add_profile_caveat(
    manifest: dict[str, Any],
    scaffold_table: dict[str, Any],
    *,
    table_iri: str,
    profile_facts_source: str | None,
) -> None:
    caveat_iri = f"{table_iri}/caveat/external-profile-facts"
    _append_unique_strings(scaffold_table, "caveats", [caveat_iri])
    caveats = manifest.setdefault("caveats", [])
    if not isinstance(caveats, list):
        raise DoxaBaseError("scaffold caveats must be a list")
    if any(
        isinstance(item, Mapping) and item.get("iri") == caveat_iri
        for item in caveats
    ):
        return
    source_note = (
        f" Source sidecar: {profile_facts_source}."
        if profile_facts_source is not None
        else ""
    )
    caveats.append(
        {
            "iri": caveat_iri,
            "label": "External profile facts merged for review",
            "description": (
                "Aggregate profile facts were supplied by an external reviewed "
                "sidecar and merged into the Parquet scaffold. DoxaBase did no "
                f"raw-row I/O during the merge.{source_note}"
            ),
            "severity": "rc:Minor",
            "targets": [table_iri],
        }
    )


def _scaffold_table_index(tables: list[Any]) -> dict[str, dict[str, Any]]:
    table_by_iri: dict[str, dict[str, Any]] = {}
    for index, table_value in enumerate(tables, start=1):
        table = _ensure_mapping(table_value, f"scaffold.tables[{index}]")
        if not isinstance(table, dict):
            raise DoxaBaseError(f"scaffold.tables[{index}] must be mutable object")
        table_iri = _required_non_empty_string(
            table,
            "iri",
            f"scaffold.tables[{index}]",
        )
        if table_iri in table_by_iri:
            raise DoxaBaseError(f"scaffold has duplicate table iri {table_iri}")
        table_by_iri[table_iri] = table
    return table_by_iri


def _value_frequencies(value: Any, context: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise DoxaBaseError(f"{context} must be a list")
    result: list[dict[str, Any]] = []
    for index, item_value in enumerate(value, start=1):
        item = _ensure_mapping(item_value, f"{context}[{index}]")
        allowed = {"value", "frequency", "count"}
        _reject_unknown_fields(item, allowed, f"{context}[{index}]")
        if "value" not in item:
            raise DoxaBaseError(f"{context}[{index}].value is required")
        frequency_key = "frequency" if "frequency" in item else "count"
        if frequency_key not in item:
            raise DoxaBaseError(
                f"{context}[{index}] requires frequency or count"
            )
        result.append(
            {
                "value": item["value"],
                "frequency": _non_negative_int(
                    item[frequency_key],
                    f"{context}[{index}].{frequency_key}",
                ),
            }
        )
    return result


def _profile_metrics(value: Any, context: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise DoxaBaseError(f"{context} must be a list")
    result: list[dict[str, Any]] = []
    for index, item_value in enumerate(value, start=1):
        item = _ensure_mapping(item_value, f"{context}[{index}]")
        allowed = {
            "metric",
            "metric_kind",
            "value",
            "datatype",
            "lang",
            "target",
            "metric_target",
            "target_iri",
        }
        _reject_unknown_fields(item, allowed, f"{context}[{index}]")
        metric = item.get("metric", item.get("metric_kind"))
        if not isinstance(metric, str) or not metric.strip():
            raise DoxaBaseError(
                f"{context}[{index}] requires non-empty metric or metric_kind"
            )
        if "value" not in item:
            raise DoxaBaseError(f"{context}[{index}].value is required")
        metric_item: dict[str, Any] = {"metric": metric, "value": item["value"]}
        for field in ("datatype", "lang"):
            if field in item:
                metric_item[field] = item[field]
        target = item.get("target", item.get("metric_target", item.get("target_iri")))
        if target is not None:
            metric_item["target"] = target
        result.append(metric_item)
    return result


def _read_json_file(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DoxaBaseError(f"{label} file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DoxaBaseError(
            f"Could not parse {label} JSON from {path}: {exc.msg} "
            f"at line {exc.lineno} column {exc.colno}"
        ) from exc
    return _ensure_mapping(value, label)


def _required_list(value: Mapping[str, Any], field: str, context: str) -> list[Any]:
    items = value.get(field)
    if not isinstance(items, list) or not items:
        raise DoxaBaseError(f"{context}.{field} must be a non-empty list")
    return items


def _ensure_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DoxaBaseError(f"{context} must be an object")
    return value


def _reject_unknown_fields(
    value: Mapping[str, Any],
    allowed: set[str],
    context: str,
) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise DoxaBaseError(
            f"{context} has unsupported field(s): {', '.join(unknown)}"
        )


def _required_non_empty_string(
    value: Mapping[str, Any],
    field: str,
    context: str,
) -> str:
    if field not in value:
        raise DoxaBaseError(f"{context}.{field} is required")
    return _optional_non_empty_string(value, field, context)


def _optional_non_empty_string(
    value: Mapping[str, Any],
    field: str,
    context: str,
) -> str:
    item = value[field]
    if not isinstance(item, str) or not item.strip():
        raise DoxaBaseError(f"{context}.{field} must be a non-empty string")
    return item


def _non_negative_int(value: Any, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise DoxaBaseError(f"{context} must be a non-negative integer")
    return value


def _string_list(value: Any, context: str) -> list[str]:
    if not isinstance(value, list):
        raise DoxaBaseError(f"{context} must be a list")
    result: list[str] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            raise DoxaBaseError(f"{context}[{index}] must be a non-empty string")
        result.append(item)
    return result


def _append_unique_strings(
    value: dict[str, Any],
    field: str,
    additions: list[str],
) -> None:
    existing = value.get(field, [])
    if existing is None:
        existing = []
    if not isinstance(existing, list):
        raise DoxaBaseError(f"{field} must be a list")
    combined: list[str] = []
    for item in [*existing, *additions]:
        if item not in combined:
            combined.append(item)
    value[field] = combined


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Merge reviewed aggregate profile facts into a DoxaBase "
            "profile-to-capsule manifest scaffold."
        ),
    )
    parser.add_argument(
        "--scaffold",
        required=True,
        help="Path to a doxabase.profile_to_capsule_manifest.v1 scaffold JSON.",
    )
    parser.add_argument(
        "--profile-facts",
        required=True,
        help="Path to a doxabase.reviewed_profile_facts.v1 JSON sidecar.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path for the merged reviewed manifest JSON.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing output manifest.",
    )
    parser.add_argument(
        "--no-profile-caveat",
        action="store_true",
        help="Do not add per-table external-profile caveats.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        manifest = write_merged_profile_manifest(
            args.output,
            scaffold_path=args.scaffold,
            profile_facts_path=args.profile_facts,
            overwrite=args.overwrite,
            add_profile_caveat=not args.no_profile_caveat,
        )
    except DoxaBaseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            merge_summary(manifest, output_path=args.output),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
