"""L1 capsule access: open the capsule read-only, nothing else.

The workbench never writes to a capsule (doc 13 decision 1: "agents write,
humans see"). Every route opens its own short-lived read-only connection;
sqlite3 connections are not safe to share across the thread pool FastAPI
runs sync routes on, and opening one against a small capsule file is cheap
(no schema/seed work happens for read_only=True).
"""
from __future__ import annotations

import os
from pathlib import Path

from doxabase import DoxaBase

CAPSULE_PATH_ENV = "WORKBENCH_CAPSULE_PATH"


def capsule_path() -> Path:
    raw = os.environ.get(CAPSULE_PATH_ENV)
    if not raw:
        raise RuntimeError(
            f"{CAPSULE_PATH_ENV} is not set. Point the workbench at a capsule, "
            f"e.g. {CAPSULE_PATH_ENV}=/path/to/capsule.sqlite uvicorn workbench.app:app"
        )
    path = Path(raw)
    if not path.exists():
        raise RuntimeError(f"Capsule not found: {path}")
    return path


def open_capsule() -> DoxaBase:
    """Return a fresh read-only DoxaBase connection for one request."""
    return DoxaBase.open_readonly(capsule_path())
