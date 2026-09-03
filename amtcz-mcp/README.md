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

```bash
pipx install <path-or-git-url>/amtcz-mcp        # preferred: isolated, on PATH
pip install --user <path-or-git-url>/amtcz-mcp  # alternative
py -m pip install --user <path-or-git-url>/amtcz-mcp   # Windows launcher
```

pip generates a native `amtcz-mcp` entry point. If it isn't resolving on
PATH in whatever environment your MCP client spawns from, `python -m
amtcz_mcp` runs the server directly, independent of PATH.

## Registering in a consumer's MCP config

The server is spawned as a direct process — no container, no volume mount,
nothing to substitute. Every tool's `root` parameter defaults to `.`, which
is simply the process's own working directory; Claude Code (and most other
clients) already set that to the project root for you.

```json
{
  "mcpServers": {
    "amtcz": {
      "command": "amtcz-mcp"
    }
  }
}
```

If `amtcz-mcp` isn't on PATH in the client's spawn environment, use the
module form instead — same effect, doesn't depend on PATH:

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

To iterate on the server, install it editable from inside `amtcz-mcp/`:

```
pip install -e ".[dev]"
```

Run it directly with `amtcz-mcp`, or `python -m amtcz_mcp`.
