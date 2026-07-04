# YOLO Container Rebuild Continuation

Written 2026-06-21T01:14:08Z before rebuilding the `hetzdev-yolo`
container. This is an operational handoff for a fresh Codex agent after the
new image starts.

## Situation

The current agent confirmed it is in container `hetzdev-yolo`, with yolo mode
enabled in the active session. The repo root resolves as:

```text
/work/doxybase -> /workspaces/doxybase
```

The tracked repository is on:

```text
master at 52c0cd2 Record profile handoff retest outcome
origin/master also at 52c0cd2
```

Current local status before rebuild:

```text
## master...origin/master
 M .gitignore
?? .doxybase.sqlite
?? docs/agent/ais-duckdb-doxybase-observations.md
?? examples/session-observations/
?? handoff/
```

The `.gitignore` change is:

```diff
+# Codex run artifacts
+.codex-runs/
```

The untracked `handoff/` files are operational notes for the container
transition. Do not commit them unless the user explicitly asks.

## What Was Verified

The repo baseline is healthy in the current container:

```bash
uv run pytest -q
# 128 passed, 139 warnings in 36.07s

uv run python tools/validate_rdf.py
# ontology and fixture RDF parsed; AIS and Polymarket fixtures SHACL conform
```

The warnings are known RDFLib deprecations around Dataset/ConjunctiveGraph/TriG
internals.

Codex CLI is installed and authenticated:

```text
codex-cli 0.141.0
model = "gpt-5.5"
model_reasoning_effort = "xhigh"
project /workspaces/doxybase is trusted
```

Nested yolo `codex exec` runs worked.

## MCP Server Setup

The DoxaBase MCP server was registered in the current container with:

```bash
codex mcp add doxabase -- bash -lc 'cd /workspaces/doxybase && uv run python -m doxabase.mcp_server --capsule /workspaces/doxybase/.doxybase.sqlite'
```

`codex mcp list` then showed:

```text
doxabase  bash  -lc cd /workspaces/doxybase && uv run python -m doxabase.mcp_server --capsule /workspaces/doxybase/.doxybase.sqlite  enabled
```

A nested Codex smoke trial successfully called:

- `doxabase.list_docs`
- `doxabase.get_doc`
- `doxabase.graph_overview`

Its final report was written to:

```text
/tmp/doxabase-runs/mcp-smoke/final.md
```

That `/tmp` artifact will probably not survive a rebuild.

Important: this current desktop thread probably did not hot-load the new MCP
tools, but new/nested Codex sessions did see them.

## Container Tooling Notes

Current useful tools:

- `codex`
- `uv`
- Python 3.12
- `jq`
- `rg`
- `git`

Current missing/limited tools:

- no `sqlite3` CLI
- no passwordless `sudo`
- `/runs` was not writable in the old image

Python's built-in `sqlite3` was enough for capsule inspection, so the missing
CLI was not blocking. If the rebuilt image makes `/runs` writable, prefer it for
durable run prompts/reports; otherwise use `/tmp/doxabase-runs` for ephemeral
trial artifacts and `.codex-runs/` for repo-local ignored artifacts.

## Product Understanding

DoxaBase is a local RDF memory capsule for data projects. The important product
shape is not "metadata catalog with RDF inside"; it is preserving agent
judgement as graph-shaped working memory.

The core loop is:

1. Record point-in-time/source-scoped observations.
2. Synthesize related observations/claims/evidence into patterns.
3. Systematise durable parts into map facts, ontology terms, shapes, caveats,
   and history.

Staged revisions are reviewable graph-thinking artifacts, not an approval
bureaucracy. They should preserve bold but labelled hunches and alternative RDF
framings without forcing every insight into an existing helper template.

## What To Read First

After rebuild, start with:

```bash
sed -n '1,220p' AGENTS.md
sed -n '1,220p' README.md
sed -n '1,380p' ARCHITECTURE.md
sed -n '1,240p' docs/agent/start-here.md
sed -n '1,340p' docs/agent/field-trials.md
sed -n '1,340p' docs/agent/staged-revisions.md
sed -n '1,260p' docs/agent/executable-catalog.md
```

Also read:

```text
handoff/container-worker-handoff.md
handoff/container-builder-handoff.md
```

if they survived the rebuild.

## Recommended Next Work

The user explicitly prefers too many sub-agent trials over too few. Treat
sub-agent trials as first-class product research, not garnish.

Best next loop:

1. Run a focused staged-revision field trial in a scratch capsule.
2. Include at least one awkward modelling hunch with multiple RDF framings.
3. Make one staged proposal stale by mutating the graph.
4. Ask a fresh/nested agent to recover using:
   - `list_graph_revisions(include_apply_checks=True)`
   - `describe_staged_revision`
   - `export_staged_revisions`
   - `check_staged_revision_apply`
   - `restage_staged_revision`
5. Preserve the prompt, final report, scratch capsule path, exports, and product
   signal.
6. Implement the smallest coherent fix the trial reveals.
7. Run focused tests, then:

```bash
uv run pytest
uv run python tools/validate_rdf.py
git diff --check
```

Likely implementation areas if the trial confirms them:

- better revision lineage/thread summaries;
- grouped stale-alternative review ergonomics;
- clearer semantic drift triage when snapshot drift is probably unrelated;
- docs/API guidance for fresh agents inheriting staged proposals.

After that, do an AIS executable-catalog loop: enrich the AIS fixture enough
that `DailyIndex` carries the real index schema/path distinction and query
context warnings become more useful before attempting query generation.

Defer full SQL generation and hybrid search until graph content and handoff
retrieval are stronger.

## Suggested Nested Trial Command

Once MCP is configured in the rebuilt image:

```bash
mkdir -p /runs/doxabase-trials || mkdir -p /tmp/doxabase-runs

codex exec \
  -C /workspaces/doxybase \
  --dangerously-bypass-approvals-and-sandbox \
  --add-dir /tmp \
  --output-last-message /tmp/doxabase-runs/staged-trial-final.md \
  - < /tmp/doxabase-runs/staged-trial-prompt.md
```

If `/runs` is writable and persistent in the new image, use `/runs/...` instead
of `/tmp/...`.

## What The User Can Help With

The user asked how to help. Good asks, if still needed after rebuild:

- make `/runs` writable and persistent across container rebuilds;
- ensure the DoxaBase MCP server is pre-registered or easy to register;
- include user-space tools such as `sqlite3` CLI if convenient;
- provide read-only credential/profile names for real AIS/MinIO/S3 trials when
  those trials are explicitly in scope;
- clarify push policy/credentials for long unattended work checkpoints.

Do not read or print secrets. Use credential references/profile names in graph
facts, not secret values.

