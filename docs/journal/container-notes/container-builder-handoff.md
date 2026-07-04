# Container Builder Handoff

This note is for the agent or human building a disposable container where Codex
can work on DoxaBase with no approval interruptions.

The goal is not to make Codex safe by asking it fewer things. The goal is to
make the container safe enough that Codex can act freely inside it.

## Desired Outcome

Build a container that can:

- run Codex non-interactively for long unattended DoxaBase development loops;
- run DoxaBase tests and RDF validation;
- run nested Codex field trials when useful;
- write commits in the copied repository;
- optionally push to the DoxaBase remote when the worker reaches a natural final
  checkpoint;
- preserve reports, logs, scratch capsules, and exported graph artifacts for
  later review.

Codex should be able to run with:

```bash
codex exec \
  -C /work/doxabase \
  --dangerously-bypass-approvals-and-sandbox \
  --output-last-message /runs/final-report.md \
  - < /runs/prompt.md
```

Equivalent explicit form:

```bash
codex exec \
  -C /work/doxabase \
  --sandbox danger-full-access \
  --ask-for-approval never \
  --output-last-message /runs/final-report.md \
  - < /runs/prompt.md
```

Use the first form only inside a container or similarly isolated environment.

## Security Boundary

The container should be permission-rich inside narrow walls.

Do:

- run as a non-root user;
- copy or mount only the DoxaBase repo and an artifacts directory;
- keep `/runs` or a similar directory persistent outside the container;
- pass secrets at runtime, not baked into the image;
- use scoped, short-lived credentials where possible;
- make Git credentials repo-scoped;
- make S3 credentials read-only and prefix-scoped unless a specific test needs
  broader access;
- set CPU, memory, disk, and wall-clock limits if the runtime supports them;
- keep logs and final reports outside the ephemeral container filesystem.

Do not:

- mount the Docker socket;
- mount the host root filesystem;
- mount the host SSH agent unless you intentionally accept that risk;
- mount broad `~/.ssh`, `~/.aws`, or `~/.codex` directories;
- put OpenAI, GitHub, or AWS credentials in the image;
- give the container access to unrelated repos or local data.

## Suggested Filesystem Layout

```text
/work/doxabase/       copied repository
/runs/                persistent run prompts, reports, logs, exports
/tmp/                 disposable scratch capsules and sub-agent artifacts
```

If the repo is bind-mounted from the host instead of copied, mount only that repo
read-write. Do not mount the host home directory.

## Base Tooling

Install:

- Python 3.12 or newer;
- `uv`;
- Git;
- Codex CLI;
- `curl`, `ca-certificates`, `jq`, `ripgrep`;
- a compiler/build toolchain if Python wheels need local builds;
- DuckDB CLI or Python package support if dataset profiling trials need it;
- AWS CLI or another S3 access tool only if trials need S3 access.

For Codex CLI installation, prefer the current official installer for the
environment. For unattended Linux install, the documented shape is:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | CODEX_NON_INTERACTIVE=1 sh
```

Then verify:

```bash
codex --version
codex exec --help
```

## Authentication

Use one of these approaches for Codex:

- `CODEX_ACCESS_TOKEN` for ChatGPT/Codex managed automation when available.
- `CODEX_API_KEY` for a single `codex exec` invocation if API-key auth is the
  intended automation route.

Avoid job-wide API-key exposure when running repository-controlled code. Prefer
passing secrets only to the Codex process or a narrow wrapper script.

For GitHub:

- use a fine-grained token or deploy key limited to this repository;
- configure the Git author identity in the container;
- prefer branch pushes unless the user has explicitly authorised direct pushes.

For S3:

- use read-only credentials for test datasets by default;
- scope to the exact bucket and prefixes needed;
- avoid printing environment variables or credential files;
- treat access failures as product signal unless the trial is specifically
  about fixing infrastructure.

## Network

Codex needs outbound network access to reach the model service. The container may
also need GitHub, Python package indexes, and S3 endpoints.

If you can constrain egress, allow only what the run needs:

- Codex/OpenAI endpoints;
- GitHub if pushing or fetching;
- package indexes during setup;
- S3 endpoints for approved data trials.

If egress is broad, keep the credential scope tight.

## DoxaBase Bootstrap Check

From the repo root:

```bash
uv sync
uv run pytest
uv run python tools/validate_rdf.py
git status --short
```

Expected current baseline before local handoff files:

- tracked worktree clean at commit `52c0cd2`;
- known local untracked artifacts may include `.doxybase.sqlite`,
  `docs/agent/ais-duckdb-doxybase-observations.md`, and
  `examples/session-observations/`;
- the local `handoff/` files are for this container transition and do not need
  to be committed unless the user later asks.

## Smoke Test A Codex Run

Create a tiny prompt under `/runs/smoke-prompt.md`:

```markdown
You are in a DoxaBase container smoke test.

Read AGENTS.md and report:

1. current branch and latest commit
2. whether `uv run pytest` passes
3. whether `uv run python tools/validate_rdf.py` passes
4. any setup issue that would block unattended work

Do not make code changes.
```

Run:

```bash
codex exec \
  -C /work/doxabase \
  --dangerously-bypass-approvals-and-sandbox \
  --output-last-message /runs/smoke-final.md \
  - < /runs/smoke-prompt.md
```

Keep both the prompt and final report.

## Launching The Real Worker

Once the smoke test passes, run Codex with the worker handoff as its prompt:

```bash
codex exec \
  -C /work/doxabase \
  --dangerously-bypass-approvals-and-sandbox \
  --output-last-message /runs/doxabase-worker-final.md \
  - < /work/doxabase/handoff/container-worker-handoff.md
```

If the account supports an explicit stronger model and the run is exploratory,
add the appropriate `--model` flag. If the model alias is unavailable, use the
best configured Codex model rather than blocking on model selection.

## Acceptance Checklist

The container is ready when:

- `codex exec --help` shows `--dangerously-bypass-approvals-and-sandbox`;
- Codex can complete the smoke prompt without approvals;
- `uv sync`, `uv run pytest`, and `uv run python tools/validate_rdf.py` pass;
- `/runs` persists after container exit;
- the worker can write files and commits in `/work/doxabase`;
- Git push works if push credentials were intentionally supplied;
- S3 read access works if S3 trials are in scope;
- no broad host credentials or host control sockets are mounted.

