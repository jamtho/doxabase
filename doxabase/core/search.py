"""Lexical FTS search over graph terms.

Mechanically split from core.py; methods are verbatim. Part of the
DoxaBase facade via SearchMixin.
"""
from __future__ import annotations

from doxabase.core._shared import *  # noqa: F401,F403
from doxabase.core._types import *  # noqa: F401,F403


class SearchMixin:
    def search(
        self,
        query: str,
        *,
        graph: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResults:
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
        total_count = int(
            self._conn.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM literal_search
                WHERE literal_search MATCH ?
                  {graph_filter}
                """,
                [fts_query, *graph_params],
            ).fetchone()["count"]
        )
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
              {graph_filter}
            ORDER BY bm25(literal_search), graph, subject, predicate
            LIMIT ? OFFSET ?
            """,
            [fts_query, *graph_params, limit, offset],
        ).fetchall()
        if total_count == 0 and len(search_tokens) > 1:
            rows = self._co_mentioned_search_rows(
                search_tokens,
                graphs,
                limit=limit,
                offset=offset,
            )
            total_count = self._co_mentioned_search_row_count(
                search_tokens,
                graphs,
            )

        ontology_graphs = self._expand_graphs(["ontology"])
        matches = [
            SearchMatch(
                iri=row["subject"],
                graph=row["graph"],
                label=self._display_label_from_graphs(
                    self._lookup_graphs([row["graph"]]),
                    row["subject"],
                ),
                types=self._types(row["graph"], row["subject"]),
                predicate=row["predicate"],
                predicate_label=self._label_from_graphs(
                    ontology_graphs,
                    row["predicate"],
                ),
                text=row["text"],
                snippet=row["snippet"],
            )
            for row in rows
        ]
        returned_count = len(matches)
        next_offset = (
            offset + returned_count
            if offset + returned_count < total_count
            else None
        )
        scope_hint = self._search_scope_hint(
            query=query,
            graph=graph,
            matches=matches,
            limit=limit,
        )
        if scope_hint is not None:
            suggested_next_actions = scope_hint.suggested_next_actions
        elif not matches:
            suggested_next_actions = self._search_no_match_actions(
                query=query,
                graph=graph,
                limit=limit,
            )
        else:
            suggested_next_actions = []
        if next_offset is not None and scope_hint is None:
            suggested_next_actions = [
                *suggested_next_actions,
                self._search_next_page_action(
                    query=query,
                    graph=graph,
                    limit=limit,
                    offset=next_offset,
                ),
            ]
        return SearchResults(
            query=query,
            graph=graph,
            matches=matches,
            limit=limit,
            offset=offset,
            returned_count=returned_count,
            total_count=total_count,
            omitted_count=max(total_count - offset - returned_count, 0),
            has_more=next_offset is not None,
            next_offset=next_offset,
            scope_hint=scope_hint,
            suggested_next_actions=suggested_next_actions,
        )
    def _search_scope_hint(
        self,
        *,
        query: str,
        graph: str | None,
        matches: list[SearchMatch],
        limit: int,
    ) -> SearchScopeHint | None:
        if graph is not None or not matches:
            return None
        seed_graphs = sorted(
            {match.graph for match in matches if match.graph in SEED_GRAPH_NAMES}
        )
        if not seed_graphs:
            return None
        seed_match_count = sum(1 for match in matches if match.graph in SEED_GRAPH_NAMES)
        project_match_count = len(matches) - seed_match_count
        if seed_match_count <= project_match_count:
            return None
        actions = [
            self._search_scoped_retry_action(query=query, graph=retry_graph, limit=limit)
            for retry_graph in SEARCH_SCOPE_HINT_GRAPHS
        ]
        return SearchScopeHint(
            status="seed_heavy_unscoped_results",
            message=(
                "Unscoped search results are dominated by immutable seed graphs. "
                "If project context was intended, retry with a project graph scope."
            ),
            seed_match_count=seed_match_count,
            project_match_count=project_match_count,
            seed_graphs=seed_graphs,
            suggested_graphs=list(SEARCH_SCOPE_HINT_GRAPHS),
            suggested_next_actions=actions,
        )
    def _search_scoped_retry_action(
        self,
        *,
        query: str,
        graph: str,
        limit: int,
    ) -> SuggestedNextAction:
        arguments = {
            "query": query,
            "graph": graph,
            "limit": limit,
            "offset": 0,
        }
        return SuggestedNextAction(
                   tool="doxabase.search",
                   args=arguments,
                   reason="Unscoped search results are seed-heavy; retrying a project graph "
                "scope can surface current map facts, observations, patterns, or "
                "evidence without seed ontology noise.",
               )
    def _search_no_match_actions(
        self,
        *,
        query: str,
        graph: str | None,
        limit: int,
    ) -> list[SuggestedNextAction]:
        retry_graph = graph or "map"
        actions: list[SuggestedNextAction] = []
        seen: set[tuple[str, str]] = set()

        for retry_query in self._search_no_match_retry_queries(query):
            if retry_query == query.strip().lower() and graph == retry_graph:
                continue
            self._append_unique_suggested_action(
                actions,
                seen,
                self._search_no_match_retry_action(
                    query=retry_query,
                    graph=retry_graph,
                    limit=limit,
                ),
            )

        browse_text = self._search_no_match_browse_text(query)
        if browse_text is not None:
            self._append_unique_suggested_action(
                actions,
                seen,
                self._search_no_match_entity_browse_action(
                    text=browse_text,
                    graph=retry_graph,
                    limit=limit,
                ),
            )

        if graph is not None:
            self._append_unique_suggested_action(
                actions,
                seen,
                self._search_no_match_unscoped_retry_action(
                    query=query,
                    limit=limit,
                ),
            )

        if graph != "history":
            self._append_unique_suggested_action(
                actions,
                seen,
                self._search_no_match_staged_payload_action(
                    query=query,
                    limit=limit,
                ),
            )
        return actions
    @staticmethod
    def _append_unique_suggested_action(
        actions: list[SuggestedNextAction],
        seen: set[tuple[str, str]],
        action: SuggestedNextAction,
    ) -> None:
        action_key = (
            action.tool,
            json.dumps(to_jsonable(action.args), sort_keys=True),
        )
        if action_key in seen:
            return
        seen.add(action_key)
        actions.append(action)
    @staticmethod
    def _search_no_match_retry_queries(query: str) -> list[str]:
        stop_tokens = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "ask",
            "asks",
            "be",
            "but",
            "by",
            "can",
            "do",
            "does",
            "for",
            "from",
            "how",
            "in",
            "into",
            "is",
            "it",
            "its",
            "of",
            "on",
            "or",
            "that",
            "the",
            "this",
            "to",
            "user",
            "what",
            "when",
            "where",
            "which",
            "why",
            "with",
            "without",
        }
        retry_queries: list[str] = []
        for token in _search_tokens(query):
            if token in stop_tokens or len(token) < 2:
                continue
            if token not in retry_queries:
                retry_queries.append(token)
            if len(retry_queries) >= 3:
                break
        return retry_queries
    @classmethod
    def _search_no_match_browse_text(cls, query: str) -> str | None:
        retry_queries = cls._search_no_match_retry_queries(query)
        return retry_queries[0] if retry_queries else None
    def _search_no_match_retry_action(
        self,
        *,
        query: str,
        graph: str,
        limit: int,
    ) -> SuggestedNextAction:
        arguments = {
            "query": query,
            "graph": graph,
            "limit": limit,
            "offset": 0,
        }
        return SuggestedNextAction(
                   tool="doxabase.search",
                   args=arguments,
                   reason="No lexical matches were found for the full query. Retrying a "
                "shorter distinctive term in a project graph can find resources "
                "whose stored wording uses different synonyms.",
               )
    def _search_no_match_entity_browse_action(
        self,
        *,
        text: str,
        graph: str,
        limit: int,
    ) -> SuggestedNextAction:
        arguments = {
            "graph": graph,
            "text": text,
            "limit": limit,
            "offset": 0,
        }
        return SuggestedNextAction(
                   tool="doxabase.list_entities",
                   args=arguments,
                   reason="No search match was found; browsing resource labels, IRIs, and "
                "literal-bearing subjects by one distinctive term can identify a "
                "seed for describe_dataset, describe_resource, or a context slice.",
               )
    def _search_no_match_unscoped_retry_action(
        self,
        *,
        query: str,
        limit: int,
    ) -> SuggestedNextAction:
        arguments = {
            "query": query,
            "graph": None,
            "limit": limit,
            "offset": 0,
        }
        return SuggestedNextAction(
                   tool="doxabase.search",
                   args=arguments,
                   reason="The scoped search had no matches. An unscoped retry can reveal "
                "observations, patterns, evidence, ontology, or history matches "
                "outside the requested graph.",
               )
    def _search_next_page_action(
        self,
        *,
        query: str,
        graph: str | None,
        limit: int,
        offset: int,
    ) -> SuggestedNextAction:
        arguments: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "offset": offset,
        }
        if graph is not None:
            arguments["graph"] = graph
        return SuggestedNextAction(
                   tool="doxabase.search",
                   args=arguments,
                   reason="More search matches exist beyond the returned page.",
               )
    def _co_mentioned_search_rows(
        self,
        tokens: list[str],
        graphs: list[str],
        *,
        limit: int,
        offset: int,
    ) -> list[sqlite3.Row]:
        return self._co_mentioned_search_selected_rows(
            tokens,
            graphs,
        )[offset : offset + limit]
    def _co_mentioned_search_row_count(
        self,
        tokens: list[str],
        graphs: list[str],
    ) -> int:
        return len(self._co_mentioned_search_selected_rows(tokens, graphs))
    def _co_mentioned_search_selected_rows(
        self,
        tokens: list[str],
        graphs: list[str],
    ) -> list[sqlite3.Row]:
        graph_filter, graph_params = self._graph_filter(graphs)
        fts_query = _fts_or_query_from_tokens(tokens)
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
              {graph_filter}
            ORDER BY graph, subject, predicate
            """,
            [fts_query, *graph_params],
        ).fetchall()
        grouped: dict[str, tuple[set[str], list[sqlite3.Row]]] = {}
        for row in rows:
            matched_tokens = {
                token for token in tokens if token in row["text"].lower()
            }
            if not matched_tokens:
                continue
            context_key = self._search_context_key(graphs, row["subject"])
            token_set, grouped_rows = grouped.setdefault(context_key, (set(), []))
            token_set.update(matched_tokens)
            grouped_rows.append(row)

        required_tokens = set(tokens)
        selected_rows: list[sqlite3.Row] = []
        seen: set[tuple[str, str, str, str]] = set()
        for context_key, (token_set, grouped_rows) in sorted(grouped.items()):
            if not required_tokens.issubset(token_set):
                continue
            for row in grouped_rows:
                row_key = (
                    row["graph"],
                    row["subject"],
                    row["predicate"],
                    row["text"],
                )
                if row_key in seen:
                    continue
                seen.add(row_key)
                selected_rows.append(row)
        return selected_rows
    def _search_context_key(self, graphs: list[str], subject: str) -> str:
        return self._first_owner_dataset_iri(graphs, subject) or subject
    @staticmethod
    def _missing_storage_partial_token_matches(
        dataset_tokens: set[str],
        access_tokens: set[str],
    ) -> list[str]:
        matches: set[str] = set()
        for dataset_token in dataset_tokens:
            for access_token in access_tokens:
                if dataset_token == access_token:
                    continue
                if (
                    len(dataset_token) >= 5
                    and dataset_token in access_token
                ) or (
                    len(access_token) >= 5
                    and access_token in dataset_token
                ):
                    matches.add(f"{dataset_token}:{access_token}")
        return sorted(matches)
    @staticmethod
    def _contains_name_like_token(text_lower: str, needle_lower: str) -> bool:
        if not needle_lower:
            return False
        return (
            re.search(
                rf"(?<![A-Za-z0-9]){re.escape(needle_lower)}(?![A-Za-z0-9])",
                text_lower,
            )
            is not None
        )
    def _predicate_hint_tokens(self, local_name: str) -> set[str]:
        spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", local_name)
        return {
            token.lower()
            for token in re.findall(r"[A-Za-z0-9]+", spaced)
            if token.lower() not in {"a", "an", "by", "has", "is", "of", "the"}
        }
    def _create_search_index(self) -> None:
        self._conn.execute(SEARCH_INDEX_SQL)
    def _rebuild_search_index(self, *, raise_on_failure: bool = True) -> None:
        try:
            self._rebuild_search_index_once()
            self._search_index_error = None
        except sqlite3.Error as exc:
            self._conn.rollback()
            self._search_index_error = str(exc)
            message = (
                "DoxaBase search index rebuild failed; graph data was preserved, "
                "but lexical search may be stale or unavailable."
            )
            if "readonly" in str(exc).lower() or "read-only" in str(exc).lower():
                message += (
                    " SQLite reported a read-only database; use "
                    "DoxaBase.open_readonly(path) for non-mutating inspection of "
                    "copied, mounted, or permission-restricted capsules."
                )
            if raise_on_failure:
                raise DoxaBaseError(message) from exc
            warnings.warn(message, RuntimeWarning, stacklevel=2)
    def _rebuild_search_index_once(self) -> None:
        self._conn.execute("DROP TABLE IF EXISTS literal_search")
        self._create_search_index()
        self._conn.execute(
            """
            INSERT INTO literal_search
                (rowid, graph, subject, subject_kind, predicate, text)
            SELECT rowid, graph, subject, subject_kind, predicate, object
            FROM quads
            WHERE object_kind IN ('literal', 'uri')
            """
        )
        self._conn.commit()
