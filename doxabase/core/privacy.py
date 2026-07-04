"""Sensitive-literal scanning and export preflight.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via PrivacyMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class PrivacyMixin:
    @contextmanager
    def _preflight_clone(self) -> Iterator["DoxaBase"]:
        clone = object.__new__(DoxaBase)
        clone.path = Path(":memory:")
        clone.read_only = False
        clone._conn = sqlite3.connect(":memory:")
        clone._conn.row_factory = sqlite3.Row
        clone._search_index_error = None
        clone._staged_apply_check_cache = None
        self._conn.backup(clone._conn)
        try:
            yield clone
        finally:
            clone.close()
    def _preflight_source_span_reuse(
        self,
        *,
        source_span_iri: str | None,
        source_path: str,
        source_section: str | None = None,
        start_line: int | None = None,
        end_line: int | None = None,
        source_kind: str | None = None,
    ) -> None:
        if source_span_iri is None:
            return
        source_span_value = source_span_iri.strip()
        if not source_span_value:
            return

        def reject_conflicting(
            predicate: str,
            expected: str,
        ) -> None:
            existing_values = set(
                self._objects(["evidence"], source_span_value, predicate)
            )
            if existing_values and existing_values != {expected}:
                raise DoxaBaseError(
                    "source_span_iri reuses an existing source span with "
                    f"conflicting {predicate}"
                )

        reject_conflicting("rc:sourcePath", source_path)
        if source_section is not None:
            reject_conflicting("rc:sourceSection", source_section)
        if start_line is not None:
            reject_conflicting("rc:startLine", str(start_line))
        if end_line is not None:
            reject_conflicting("rc:endLine", str(end_line))
        source_kind_value = (
            source_kind.strip()
            if source_kind and source_kind.strip()
            else None
        )
        if source_kind_value is not None:
            reject_conflicting("rc:sourceKind", self.expand_iri(source_kind_value))
    def scan_sensitive_literals(
        self,
        graphs: Iterable[str] | str | None = None,
        *,
        limit: int = 50,
    ) -> SensitiveLiteralScan:
        if limit < 1:
            raise DoxaBaseError("limit must be at least 1")
        graph_names = self._graph_names_for_export(
            graphs,
            default_preset="project",
        )
        rows = self._sensitive_literal_rows(graph_names)
        matches: list[SensitiveLiteralMatch] = []
        omitted = 0
        for row in rows:
            match_kind, redacted_snippet = self._sensitive_literal_match(
                str(row["term_value"])
            )
            if match_kind is None or redacted_snippet is None:
                continue
            if len(matches) < limit:
                matches.append(
                    SensitiveLiteralMatch(
                        graph=str(row["graph"]),
                        subject=self._redact_sensitive_context_value(
                            str(row["subject"])
                        ),
                        predicate=self._redact_sensitive_context_value(
                            str(row["predicate"])
                        ),
                        object_kind=str(row["object_kind"]),
                        term_position=str(row["term_position"]),
                        term_kind=str(row["term_kind"]),
                        match_kind=match_kind,
                        redacted_snippet=redacted_snippet,
                    )
                )
            else:
                omitted += 1
        warnings = self._sensitive_literal_warnings(
            match_count=len(matches) + omitted,
            omitted_match_count=omitted,
        )
        return SensitiveLiteralScan(
            graphs=graph_names,
            match_count=len(matches) + omitted,
            sensitive_literal_count=len(matches) + omitted,
            returned_match_count=len(matches),
            omitted_match_count=omitted,
            limit=limit,
            matches=matches,
            warnings=warnings,
        )
    def _sensitive_literal_rows(self, graph_names: list[str]) -> list[sqlite3.Row]:
        if not graph_names:
            return []
        placeholders = ", ".join("?" for _ in graph_names)
        return list(
            self._conn.execute(
                f"""
                SELECT
                    graph,
                    subject,
                    predicate,
                    object_kind,
                    'subject' AS term_position,
                    subject_kind AS term_kind,
                    subject AS term_value
                FROM quads
                WHERE graph IN ({placeholders})
                  AND subject_kind = 'uri'
                UNION ALL
                SELECT
                    graph,
                    subject,
                    predicate,
                    object_kind,
                    'predicate' AS term_position,
                    'uri' AS term_kind,
                    predicate AS term_value
                FROM quads
                WHERE graph IN ({placeholders})
                UNION ALL
                SELECT
                    graph,
                    subject,
                    predicate,
                    object_kind,
                    'object' AS term_position,
                    object_kind AS term_kind,
                    object AS term_value
                FROM quads
                WHERE graph IN ({placeholders})
                  AND object_kind IN ('literal', 'uri')
                ORDER BY graph, subject, predicate, term_position, term_value
                """,
                [*graph_names, *graph_names, *graph_names],
            )
        )
    def _sensitive_literal_match(
        self,
        value: str,
    ) -> tuple[str | None, str | None]:
        for match_kind, pattern in SENSITIVE_LITERAL_PATTERNS:
            match = pattern.search(value)
            if match is None:
                continue
            return match_kind, self._redacted_sensitive_snippet(
                value,
                match.start(),
                match.end(),
                match_kind,
            )
        return None, None
    @staticmethod
    def _shareability_hint_codes_for_value(value: str) -> list[str]:
        return [
            hint_code
            for hint_code, pattern in SHAREABILITY_HINT_PATTERNS
            if pattern.search(value)
        ]
    def _shareability_hints_for_values(
        self,
        values: Iterable[str | None],
    ) -> list[str]:
        hints: list[str] = []
        for value in values:
            if value is None:
                continue
            hints.extend(self._shareability_hint_codes_for_value(str(value)))
        return list(dict.fromkeys(hints))
    def _shareability_hints_for_graphs(self, graph_names: list[str]) -> list[str]:
        return self._shareability_hints_for_values(
            str(row["term_value"]) for row in self._sensitive_literal_rows(graph_names)
        )
    def _shareability_hints_for_context_triples(
        self,
        triples: Iterable[ResourceTriple],
    ) -> list[str]:
        values: list[str] = []
        for triple in triples:
            if triple.subject_kind == "uri":
                values.append(triple.subject)
            values.append(triple.predicate)
            if triple.object_kind in {"literal", "uri"}:
                values.append(triple.object)
        return self._shareability_hints_for_values(values)
    def _shareability_hints_for_text(self, text: str) -> list[str]:
        return self._shareability_hints_for_values([text])
    @staticmethod
    def _markdown_shareability_hint_codes_for_line(line: str) -> list[str]:
        hint_codes = DoxaBase._shareability_hint_codes_for_value(line)
        if (
            "absolute_local_runtime_path" in hint_codes
            and '"path": "/tmp/' in line
            and (
                "doxabase.export_staged_revision" in line
                or "doxabase.export_staged_revisions" in line
                or "doxabase.export_profile_insight_review_bundle" in line
            )
        ):
            hint_codes = [
                hint_code
                for hint_code in hint_codes
                if hint_code != "absolute_local_runtime_path"
            ]
        return hint_codes
    def _shareability_hints_for_markdown(self, text: str) -> list[str]:
        hints: list[str] = []
        for line in text.splitlines():
            hints.extend(self._markdown_shareability_hint_codes_for_line(line))
        return list(dict.fromkeys(hints))
    @staticmethod
    def _shareability_hint_match_id(
        *,
        export_part: str,
        hint_code: str,
        graph: str | None = None,
        subject: str | None = None,
        predicate: str | None = None,
        object_kind: str | None = None,
        term_position: str | None = None,
        term_kind: str | None = None,
        revision_iri: str | None = None,
        line_number: int | None = None,
    ) -> str:
        digest = hashlib.sha256()
        for value in (
            export_part,
            hint_code,
            graph or "",
            subject or "",
            predicate or "",
            object_kind or "",
            term_position or "",
            term_kind or "",
            revision_iri or "",
            "" if line_number is None else str(line_number),
        ):
            digest.update(value.encode("utf-8"))
            digest.update(b"\x1f")
        return f"shareability-sha256:{digest.hexdigest()}"
    def _shareability_hint_matches_for_graphs(
        self,
        graph_names: list[str],
        *,
        export_part: str = "graphs",
        limit: int = DEFAULT_SHAREABILITY_HINT_MATCH_LIMIT,
    ) -> tuple[int, list[ShareabilityHintMatch]]:
        matches: list[ShareabilityHintMatch] = []
        match_count = 0
        for row in self._sensitive_literal_rows(graph_names):
            hint_codes = self._shareability_hint_codes_for_value(
                str(row["term_value"])
            )
            if not hint_codes:
                continue
            graph = str(row["graph"])
            subject = self._redact_sensitive_context_value(str(row["subject"]))
            predicate = self._redact_sensitive_context_value(str(row["predicate"]))
            object_kind = str(row["object_kind"])
            term_position = str(row["term_position"])
            term_kind = str(row["term_kind"])
            for hint_code in hint_codes:
                match_count += 1
                if len(matches) >= limit:
                    continue
                matches.append(
                    ShareabilityHintMatch(
                        export_part=export_part,
                        match_id=self._shareability_hint_match_id(
                            export_part=export_part,
                            hint_code=hint_code,
                            graph=graph,
                            subject=subject,
                            predicate=predicate,
                            object_kind=object_kind,
                            term_position=term_position,
                            term_kind=term_kind,
                        ),
                        hint_code=hint_code,
                        graph=graph,
                        subject=subject,
                        predicate=predicate,
                        object_kind=object_kind,
                        term_position=term_position,
                        term_kind=term_kind,
                    )
                )
        return match_count, matches
    def _shareability_hint_matches_for_context_triples(
        self,
        triples: Iterable[ResourceTriple],
        *,
        export_part: str = "context_slice",
        limit: int = DEFAULT_SHAREABILITY_HINT_MATCH_LIMIT,
    ) -> tuple[int, list[ShareabilityHintMatch]]:
        matches: list[ShareabilityHintMatch] = []
        match_count = 0
        for triple in triples:
            term_values: list[tuple[str, str, str]] = []
            if triple.subject_kind == "uri":
                term_values.append(("subject", triple.subject_kind, triple.subject))
            term_values.append(("predicate", "uri", triple.predicate))
            if triple.object_kind in {"literal", "uri"}:
                term_values.append(("object", triple.object_kind, triple.object))
            subject = self._redact_sensitive_context_value(triple.subject)
            predicate = self._redact_sensitive_context_value(triple.predicate)
            for term_position, term_kind, value in term_values:
                for hint_code in self._shareability_hint_codes_for_value(value):
                    match_count += 1
                    if len(matches) >= limit:
                        continue
                    matches.append(
                        ShareabilityHintMatch(
                            export_part=export_part,
                            match_id=self._shareability_hint_match_id(
                                export_part=export_part,
                                hint_code=hint_code,
                                graph=triple.graph,
                                subject=subject,
                                predicate=predicate,
                                object_kind=triple.object_kind,
                                term_position=term_position,
                                term_kind=term_kind,
                            ),
                            hint_code=hint_code,
                            graph=triple.graph,
                            subject=subject,
                            predicate=predicate,
                            object_kind=triple.object_kind,
                            term_position=term_position,
                            term_kind=term_kind,
                        )
                    )
        return match_count, matches
    def _shareability_hint_matches_for_markdown(
        self,
        text: str,
        *,
        export_part: str,
        limit: int = DEFAULT_SHAREABILITY_HINT_MATCH_LIMIT,
        final_privacy_warning_line_numbers: bool = False,
    ) -> tuple[int, list[ShareabilityHintMatch]]:
        matches: list[ShareabilityHintMatch] = []
        match_count = 0
        lines = text.splitlines()
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
            final_line_number = (
                line_number + inserted_line_count
                if line_number > insertion_after_line
                else line_number
            )
            for hint_code in self._markdown_shareability_hint_codes_for_line(line):
                match_count += 1
                if len(matches) >= limit:
                    continue
                matches.append(
                    ShareabilityHintMatch(
                        export_part=export_part,
                        match_id=self._shareability_hint_match_id(
                            export_part=export_part,
                            hint_code=hint_code,
                            line_number=final_line_number,
                        ),
                        hint_code=hint_code,
                        line_number=final_line_number,
                    )
                )
        return match_count, matches
    @staticmethod
    def _shareability_hint_warnings(hints: Iterable[str]) -> list[str]:
        return [
            SHAREABILITY_HINT_MESSAGES[hint]
            for hint in dict.fromkeys(hints)
            if hint in SHAREABILITY_HINT_MESSAGES
        ]
    def _redact_sensitive_context_value(self, value: str) -> str:
        match_kind, redacted_snippet = self._sensitive_literal_match(value)
        if match_kind is None or redacted_snippet is None:
            return value
        return redacted_snippet
    def _privacy_redacted_resource_summary(
        self,
        summary: ResourceSummary,
    ) -> ResourceSummary:
        return ResourceSummary(
            iri=summary.iri,
            label=self._redact_sensitive_optional_text(summary.label),
            description=self._redact_sensitive_optional_text(summary.description),
            column_name=self._redact_sensitive_optional_text(summary.column_name),
            owning_dataset_iri=summary.owning_dataset_iri,
            owning_dataset_label=self._redact_sensitive_optional_text(
                summary.owning_dataset_label
            ),
        )
    def _privacy_redacted_optional_resource_summary(
        self,
        summary: ResourceSummary | None,
    ) -> ResourceSummary | None:
        if summary is None:
            return None
        return self._privacy_redacted_resource_summary(summary)
    def _privacy_redacted_source_span_description(
        self,
        span: SourceSpanDescription,
    ) -> SourceSpanDescription:
        return SourceSpanDescription(
            iri=span.iri,
            source_path=self._redact_sensitive_optional_text(span.source_path),
            source_section=self._redact_sensitive_optional_text(span.source_section),
            start_line=span.start_line,
            end_line=span.end_line,
            source_kind=span.source_kind,
            source_kind_label=self._redact_sensitive_optional_text(
                span.source_kind_label
            ),
        )
    def _privacy_redacted_evidence_description(
        self,
        evidence: EvidenceDescription,
    ) -> EvidenceDescription:
        return EvidenceDescription(
            iri=evidence.iri,
            label=self._redact_sensitive_optional_text(evidence.label),
            summary=self._redact_sensitive_optional_text(evidence.summary),
            sources=[
                self._redact_sensitive_context_value(source)
                for source in evidence.sources
            ],
            source_spans=[
                self._privacy_redacted_source_span_description(span)
                for span in evidence.source_spans
            ],
            scanned_source_handles=[
                self._redact_sensitive_context_value(handle)
                for handle in evidence.scanned_source_handles
            ],
            query_execution_status=self._redact_sensitive_optional_text(
                evidence.query_execution_status
            ),
            query_engine=self._redact_sensitive_optional_text(evidence.query_engine),
            query_hash=self._redact_sensitive_optional_text(evidence.query_hash),
        )
    def _privacy_redacted_jsonable(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._redact_sensitive_context_value(value)
        if isinstance(value, MappingABC):
            return {
                str(key): self._privacy_redacted_jsonable(item)
                for key, item in value.items()
            }
        if isinstance(value, tuple):
            return [
                self._privacy_redacted_jsonable(item)
                for item in value
            ]
        if isinstance(value, list):
            return [
                self._privacy_redacted_jsonable(item)
                for item in value
            ]
        if is_dataclass(value) and not isinstance(value, type):
            return {
                field.name: self._privacy_redacted_jsonable(
                    getattr(value, field.name)
                )
                for field in fields(value)
            }
        return value
    def _privacy_redacted_api_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._redact_sensitive_context_value(value)
        if isinstance(value, MappingABC):
            return {
                str(key): self._privacy_redacted_api_value(item)
                for key, item in value.items()
            }
        if isinstance(value, tuple):
            return tuple(self._privacy_redacted_api_value(item) for item in value)
        if isinstance(value, list):
            return [self._privacy_redacted_api_value(item) for item in value]
        if is_dataclass(value) and not isinstance(value, type):
            updates = {
                field.name: self._privacy_redacted_api_value(
                    getattr(value, field.name)
                )
                for field in fields(value)
                if field.init
            }
            return replace(value, **updates)
        return value
    def _privacy_redacted_suggested_next_action(
        self,
        action: SuggestedNextAction,
    ) -> SuggestedNextAction:
        updates = {
            field.name: self._privacy_redacted_jsonable(
                getattr(action, field.name)
            )
            for field in fields(action)
        }
        return replace(action, **updates)
    def _redact_sensitive_optional_text(
        self,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        return self._redact_sensitive_context_value(value)
    @staticmethod
    def _redacted_sensitive_snippet(
        value: str,
        start: int,
        end: int,
        match_kind: str,
    ) -> str:
        del value, start, end
        return f"[REDACTED:{match_kind}]"
    @staticmethod
    def _sensitive_literal_warnings(
        *,
        match_count: int,
        omitted_match_count: int,
    ) -> list[str]:
        if match_count == 0:
            return []
        warning = (
            "Potential sensitive graph terms detected. Review redacted scan results "
            "before sharing exports; DoxaBase preserves caller-authored graph "
            "terms and does not redact RDF automatically."
        )
        if omitted_match_count:
            warning += f" {omitted_match_count} additional match(es) omitted by limit."
        return [warning]
    @staticmethod
    def _markdown_with_privacy_warning(
        data: str,
        privacy_warnings: list[str],
    ) -> str:
        if not privacy_warnings:
            return data
        warning_lines = [
            "## Privacy Warning",
            "",
            *(f"- {warning}" for warning in privacy_warnings),
            "",
        ]
        lines = data.splitlines()
        if len(lines) >= 2 and lines[0].startswith("# ") and lines[1] == "":
            output_lines = [lines[0], "", *warning_lines, *lines[2:]]
        else:
            output_lines = [*warning_lines, *lines]
        return "\n".join(output_lines).rstrip() + "\n"
    @staticmethod
    def _preflight_optional_string(name: str, value: Any) -> None:
        if value is not None and not isinstance(value, str):
            raise DoxaBaseError(f"{name} must be a string")
    @staticmethod
    def _preflight_string_values(
        name: str,
        value: Iterable[str] | str | None,
    ) -> list[str]:
        if value is None:
            values: list[Any] = []
        elif isinstance(value, str):
            values = [value]
        else:
            try:
                values = list(value)
            except TypeError as exc:
                raise DoxaBaseError(
                    f"{name} must be a string or iterable of strings"
                ) from exc
        for index, item in enumerate(values, start=1):
            if not isinstance(item, str):
                raise DoxaBaseError(f"{name}[{index}] must be a string")
        return [item.strip() for item in values if item.strip()]
    def _preflight_evidence_summary_reuse(
        self,
        evidence_iri: str,
        evidence_summary: str | None,
        *,
        field_name: str = "evidence_summary",
    ) -> None:
        if evidence_summary is None or not evidence_summary.strip():
            return
        existing_summaries = self._objects(
            ["evidence"],
            evidence_iri,
            "rc:summary",
        )
        conflicting = [
            summary for summary in existing_summaries if summary != evidence_summary
        ]
        if conflicting:
            raise DoxaBaseError(
                f"{field_name} conflicts with existing summary for evidence_iri "
                f"{evidence_iri!r}; omit {field_name}, reuse the existing summary, "
                "or use a new evidence_iri"
            )
