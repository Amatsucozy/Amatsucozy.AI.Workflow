# amtcz-mcp

An MCP (Model Context Protocol) server exposing SARIF build diagnostics,
TRX test results, and experience-memory lookup as tools — for use by any
MCP-capable agent (Claude Code, etc.) over stdio.

`amtcz-mcp` is the successor to [`amtcz-cli`](../amtcz-cli/README.md), which
is now deprecated. It is a fully independent package: no shared code and no
shared dependency with `amtcz-cli`. The old CLI's logic was reimplemented
from scratch as pure-Python extraction modules (`sarif.py`, `trx.py`,
`experiences.py`) that return structured data instead of printing tables and
exit codes — the old exit-code semantics now live in each tool result's
`verdict` field.

Runs as a plain Python process over stdio — no Docker, no container image.
`sarif_build` and `test_run` shell out to `dotnet build`/`dotnet test`, so
the machine running the server needs the .NET SDK on PATH (the same
requirement `amtcz-cli` always had — nothing new here, just no longer
hidden inside a container).

## Install

Using [uv](https://docs.astral.sh/uv/) (preferred):

```bash
uv tool install <path-or-git-url>/amtcz-mcp    # isolated, on PATH
```

Or skip installing entirely and run it ad hoc — uv fetches/builds into a
cached environment on first use and reuses it after:

```bash
uvx --from <path-or-git-url>/amtcz-mcp amtcz-mcp
```

Without uv, plain pip works too:

```bash
pipx install <path-or-git-url>/amtcz-mcp        # isolated, on PATH
pip install --user <path-or-git-url>/amtcz-mcp  # alternative
py -m pip install --user <path-or-git-url>/amtcz-mcp   # Windows launcher
```

Any of the above generates a native `amtcz-mcp` entry point. If it isn't
resolving on PATH in whatever environment your MCP client spawns from,
`python -m amtcz_mcp` runs the server directly, independent of PATH.

## Registering in a consumer's MCP config

The server is spawned as a direct process — no container, no volume mount,
nothing to substitute. Every tool's `root` parameter defaults to `.`, which
is simply the process's own working directory; Claude Code (and most other
clients) already set that to the project root for you.

With `uvx`, no separate install step is needed at all — copy
[`.mcp.json.example`](.mcp.json.example) to your target repo's `.mcp.json`
(or merge the `amtcz` entry into an existing one) and replace the
placeholder path with wherever this repo lives on your machine:

```json
{
  "mcpServers": {
    "amtcz": {
      "command": "uvx",
      "args": ["--from", "<path-or-git-url>/amtcz-mcp", "amtcz-mcp"]
    }
  }
}
```

If you installed with `uv tool install` (or plain pip/pipx) instead,
`amtcz-mcp` is already on PATH:

```json
{
  "mcpServers": {
    "amtcz": {
      "command": "amtcz-mcp"
    }
  }
}
```

Fallback if neither resolves on PATH in the client's spawn environment:

```json
{
  "mcpServers": {
    "amtcz": {
      "command": "python",
      "args": ["-m", "amtcz_mcp"]
    }
  }
}
```

## Tools at a glance

| Tool | Purpose |
| --- | --- |
| `sarif_build` | Run `dotnet build` with SARIF error logging and return a structured, error-only report. |
| `sarif_probe` | Re-extract a report from SARIF logs already on disk, without rebuilding. |
| `test_run` | Run `dotnet test` with TRX logging and return a structured, failure-only report. |
| `test_probe` | Re-read the existing TRX file without rerunning tests. |
| `exp_inventory` | List the experience-memory tag inventory (`docs/experiences/*.md`) as tag -> entry-count. |
| `exp_search` | Search experience-memory entries by tag/symptom/keyword. |

Each tool's full docstring (parameter behavior and every `verdict` value's
meaning) is visible to the calling agent through MCP tool introspection.

## Local development

To iterate on the server, from inside `amtcz-mcp/`:

```bash
uv sync --extra dev
```

This creates `.venv/` and `uv.lock` (committed, for reproducible dev
installs) and installs the package editable plus `pytest`. Run the server
with `uv run amtcz-mcp` (or `uv run python -m amtcz_mcp`), and the test
suite with `uv run pytest`.

Without uv: `pip install -e ".[dev]"`, then run with `amtcz-mcp` /
`python -m amtcz_mcp` / `pytest` as usual.
