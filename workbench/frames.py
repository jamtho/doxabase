"""The one DuckDB frame-query endpoint: read-only, capped, SELECT-only.

A described dataset points at S3 parquet via ``path_templates`` like
``s3://ais-noaa/broadcasts/{year}/ais-{date}.parquet``. We turn the first
S3 template into a glob (placeholders -> ``*``) and register it as a view
named ``frame`` that the analyst's SQL can select from. Credentials come
from the environment (MINIO_ENDPOINT / MINIO_ACCESS_KEY / MINIO_SECRET_KEY),
mirroring the AIS study's own query.py / story_kml.py convention; the
workbench never records or displays them.

Reachability (glob() against the bucket, not a full read) is cached per
glob for the process lifetime so the dataset page can decide, on every
render, whether to show the query box at all -- doc 13 4.4's "IF the
dataset's storage is reachable, else hidden".
"""
from __future__ import annotations

import os
import re
import threading

import duckdb

ROW_CAP = 500
_PLACEHOLDER = re.compile(r"\{[^}]+\}")
_LEADING_KEYWORD = re.compile(r"^\s*(WITH|SELECT)\b", re.IGNORECASE)
# Defence in depth: block statement keywords a SELECT/WITH body has no
# legitimate reason to contain, even though each query runs on a throwaway
# in-memory DuckDB connection over a read-only S3 credential.
_BLOCKED_KEYWORDS = re.compile(
    r"\b(ATTACH|DETACH|COPY|EXPORT|IMPORT|INSTALL|LOAD|PRAGMA|SET|CALL|"
    r"CREATE|INSERT|UPDATE|DELETE|DROP|ALTER|VACUUM|CHECKPOINT|GRANT)\b",
    re.IGNORECASE,
)


class FrameQueryError(ValueError):
    """A frame query was rejected or failed."""


def _data_root() -> str | None:
    """Root for LOCAL frames (WORKBENCH_DATA_ROOT, default: the capsule's
    own directory). Local path templates in dataset descriptions are
    resolved against it; anything escaping the root is refused."""
    root = os.environ.get("WORKBENCH_DATA_ROOT")
    if not root:
        capsule = os.environ.get("WORKBENCH_CAPSULE_PATH")
        if capsule:
            root = os.path.dirname(os.path.abspath(capsule))
    return os.path.realpath(root) if root else None


def frame_glob(path_templates: list[str]) -> str | None:
    """First usable path template, placeholders widened to a glob: S3
    templates pass through; relative/local templates resolve against the
    data root (and must stay inside it). None if the dataset has no
    physical layout (e.g. a logical analysis view)."""
    for template in path_templates:
        if template.startswith("s3://"):
            return _PLACEHOLDER.sub("*", template)
        root = _data_root()
        if root is None:
            continue
        widened = _PLACEHOLDER.sub("*", template)
        candidate = widened if os.path.isabs(widened) else os.path.join(root, widened)
        # realpath on the non-glob prefix so ../ cannot escape the root
        prefix = candidate.split("*", 1)[0]
        if not os.path.realpath(prefix).startswith(root + os.sep):
            continue
        return candidate
    return None


def _connect(glob: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    if not glob.startswith("s3://"):
        return con
    con.execute("INSTALL httpfs; LOAD httpfs;")
    endpoint = os.environ.get("MINIO_ENDPOINT", "")
    endpoint = endpoint.replace("http://", "").replace("https://", "")
    access_key = os.environ.get("MINIO_ACCESS_KEY")
    secret_key = os.environ.get("MINIO_SECRET_KEY")
    if not (endpoint and access_key and secret_key):
        raise FrameQueryError(
            "S3 storage is not configured (MINIO_ENDPOINT / MINIO_ACCESS_KEY / "
            "MINIO_SECRET_KEY not all set in the environment)."
        )
    con.execute(f"SET s3_endpoint='{endpoint}'")
    con.execute("SET s3_url_style='path'; SET s3_use_ssl=false; SET s3_region='local';")
    con.execute(f"SET s3_access_key_id='{access_key}'")
    con.execute(f"SET s3_secret_access_key='{secret_key}'")
    return con


_reachability_cache: dict[str, bool] = {}
_reachability_lock = threading.Lock()


def is_reachable(glob: str) -> bool:
    """Cheap reachability probe: list matching files, read none of them."""
    with _reachability_lock:
        if glob in _reachability_cache:
            return _reachability_cache[glob]
    try:
        con = _connect(glob)
        matches = con.execute(
            "SELECT * FROM glob(?) LIMIT 1", [glob]
        ).fetchall()
        ok = len(matches) > 0
    except Exception:
        ok = False
    with _reachability_lock:
        _reachability_cache[glob] = ok
    return ok


def _guard_select_only(sql: str) -> str:
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        raise FrameQueryError("Query is empty.")
    if ";" in stripped:
        raise FrameQueryError("Only a single statement is allowed.")
    if not _LEADING_KEYWORD.match(stripped):
        raise FrameQueryError("Only SELECT/WITH queries are allowed.")
    if _BLOCKED_KEYWORDS.search(stripped):
        raise FrameQueryError("Query contains a disallowed keyword.")
    return stripped


def run_query(glob: str, sql: str) -> tuple[list[str], list[tuple]]:
    """Run one read-only, row-capped SELECT against the frame named `frame`.

    Returns (column_names, rows); always at most ROW_CAP rows, regardless
    of any LIMIT in the caller's own SQL.
    """
    stripped = _guard_select_only(sql)
    con = _connect(glob)
    con.execute(f"CREATE VIEW frame AS SELECT * FROM read_parquet('{glob}')")
    capped = f"SELECT * FROM ({stripped}) AS workbench_query LIMIT {ROW_CAP}"
    try:
        result = con.execute(capped)
    except duckdb.Error as exc:
        raise FrameQueryError(str(exc)) from exc
    rows = result.fetchall()
    columns = [d[0] for d in result.description]
    return columns, rows
