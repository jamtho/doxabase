# Operator Note After Toolbelt Rebuild

Read this together with `handoff/yolo-rebuild-continuation.md` before doing
new product work.

## What Changed

The container image was rebuilt with Codex CLI pinned at `0.141.0` and a broader
system tool belt. The agent still runs as the non-root `codex` user. It does not
have `sudo` by design.

Installed system tools now include:

- C/C++ build basics: `build-essential`, `cmake`, `pkg-config`
- Python build support: `python3-dev`, `python3-pip`, `python3-venv`,
  `python-is-python3`, `libffi-dev`
- SQLite tooling: `sqlite3`, `libsqlite3-dev`
- Shell/data utilities: `jq`, `rg`, `tree`, `file`, `rsync`
- Archive tools: `zip`, `unzip`, `xz-utils`, `zstd`
- Network/process inspection: `iproute2`, `iputils-ping`, `dnsutils`,
  `netcat-openbsd`, `lsof`, `procps`
- Codex sandbox support package: `bubblewrap`

If another OS package is needed, record the package name and why. The preferred
path is to add it to the Dockerfile and rebuild, not to grant routine root.

## Paths And Persistence

The DoxaBase repo is a copied working tree in the persistent Docker volume:

```text
/workspaces/doxybase
/work/doxybase -> /workspaces/doxybase
```

Use repo-local ignored artifacts for durable run outputs:

```text
/workspaces/doxybase/.codex-runs/
```

`/tmp` is fine for scratch work but should be treated as ephemeral. Do not rely
on `/runs` unless a human explicitly adds and verifies it.

## MCP

Verify or re-register DoxaBase MCP with:

```bash
codex mcp list
codex mcp add doxabase -- bash -lc 'cd /workspaces/doxybase && uv run python -m doxabase.mcp_server --capsule /workspaces/doxybase/.doxybase.sqlite'
```

Fresh/nested Codex sessions should see the MCP tools. Existing desktop threads
may not hot-load a changed MCP tool list.

## MinIO And Secrets

MinIO read-only access is available through the `local` alias. Use capability
checks such as:

```bash
mc ls local/
mc ls local/ais-noaa/
mc ls local/enron-emails/
```

Do not print `mc alias list` in reports; it includes credentials.

## Suggested Restart Prompt

Start by reading:

```bash
sed -n '1,220p' AGENTS.md
sed -n '1,260p' handoff/yolo-rebuild-continuation.md
sed -n '1,220p' README.md
sed -n '1,340p' docs/agent/field-trials.md
sed -n '1,340p' docs/agent/staged-revisions.md
```

Then run:

```bash
uv run pytest -q
uv run python tools/validate_rdf.py
codex mcp list
```

Continue with the staged-revision sub-agent trial described in
`handoff/yolo-rebuild-continuation.md`.
