"""``doxabase-workbench capsule.sqlite`` -> http://localhost:PORT (doc 13 §1).

The console script is always registered by the core `doxabase` wheel (a pip
entry point cannot be conditional on an extra), but its runtime deps
(fastapi/uvicorn/duckdb/jinja2/...) only land with the optional `workbench`
extra -- see pyproject.toml's `[project.optional-dependencies]`. The import
is deferred into main() and guarded so a core-only install fails with one
clear line instead of a raw traceback.

Note `uvicorn` alone is *not* a reliable signal here: the core `mcp[cli]`
dependency pulls in uvicorn/starlette transitively for its own SSE/
streamable-http transport, so it is already importable in a core-only
install. `workbench.app` is what actually needs fastapi/duckdb/jinja2, so
that is the import this guards.
"""
from __future__ import annotations

import argparse
import os


def main() -> None:
    try:
        import uvicorn

        import workbench.app  # noqa: F401  (import-only: proves fastapi/duckdb/jinja2 are present)
    except ImportError as exc:
        raise SystemExit(
            "doxabase-workbench needs its optional extra: "
            'pip install "doxabase[workbench]" (missing: '
            f"{exc.name or exc})"
        ) from None

    parser = argparse.ArgumentParser(prog="doxabase-workbench")
    parser.add_argument("capsule", help="Path to a capsule .sqlite file (opened read-only)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    os.environ["WORKBENCH_CAPSULE_PATH"] = args.capsule
    uvicorn.run("workbench.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
