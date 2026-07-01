from __future__ import annotations

import os
from pathlib import Path


EXAMPLE_RUN_ROOT_ENV = "DOXABASE_EXAMPLE_RUN_ROOT"


def example_run_dir(name: str, legacy_path: str | Path) -> Path:
    root = _configured_run_root()
    if root is None:
        return Path(legacy_path)
    return root / f"doxabase-{name}"


def example_artifact(
    name: str,
    legacy_path: str | Path,
    *,
    filename: str | None = None,
) -> Path:
    root = _configured_run_root()
    if root is None:
        return Path(legacy_path)
    return root / f"doxabase-{name}" / (filename or Path(legacy_path).name)


def reset_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()


def _configured_run_root() -> Path | None:
    configured = os.environ.get(EXAMPLE_RUN_ROOT_ENV)
    if configured is None or configured == "":
        return None
    return Path(configured).expanduser()
