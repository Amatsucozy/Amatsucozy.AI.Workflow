# roslyn-mcp

MCP server that wraps `roslyn-language-server` (the official C# LSP that
powers VS Code's C# extension) and exposes it as structured tools over
stdio — for agents that speak MCP but not LSP (Devin, custom Bedrock
agents, etc.). Companion to `amtcz-mcp`: that one answers "does it build /
do tests pass"; this one answers "where is this defined / who calls it /
what breaks if I rename it" without a build.

## Prerequisites

- .NET 10 runtime + `dotnet tool install --global roslyn-language-server --prerelease`
- Python 3.10+

## Install

Using [uv](https://docs.astral.sh/uv/) (preferred):

```bash
uv tool install <path-or-git-url>/roslyn-mcp    # isolated, on PATH
```

Or skip installing entirely and run it ad hoc — uv fetches/builds into a
cached environment on first use and reuses it after:

```bash
uvx --from <path-or-git-url>/roslyn-mcp roslyn-mcp
```

Without uv, plain pip works too:

```bash
pipx install <path-or-git-url>/roslyn-mcp        # isolated, on PATH
pip install --user <path-or-git-url>/roslyn-mcp  # alternative
py -m pip install --user <path-or-git-url>/roslyn-mcp   # Windows launcher
```

Any of the above generates a native `roslyn-mcp` entry point. If it isn't
resolving on PATH in whatever environment your MCP client spawns from,
`python -m roslyn_mcp` runs the server directly, independent of PATH.

## Registering in a consumer's MCP config

The server uses its cwd as the workspace root (most clients set that to the
repo); override with `ROSLYN_MCP_ROOT`.

With `uvx`, no separate install step is needed at all — copy
[`.mcp.json.example`](.mcp.json.example) to your target repo's `.mcp.json`
(or merge the `roslyn` entry into an existing one). It installs straight
from GitHub, no local clone required:

```json
{
  "mcpServers": {
    "roslyn": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Amatsucozy/Amatsucozy.AI.Workflow.git@v1.0.0#subdirectory=roslyn-mcp",
        "roslyn-mcp"
      ],
      "env": {
        "ROSLYN_LSP_CMD": "C:/Users/<you>/.dotnet/tools/roslyn-language-server.cmd"
      }
    }
  }
}
```

Pinned to the `v1.0.0` release tag — more stable than tracking `main`, which
moves as other packages in this repo change. If you're iterating on
`roslyn-mcp` itself and want changes picked up without a `git push`
round-trip, point `--from` at a local path instead:

```json
{
  "mcpServers": {
    "roslyn": {
      "command": "uvx",
      "args": ["--from", "<path>/roslyn-mcp", "roslyn-mcp"],
      "env": {
        "ROSLYN_LSP_CMD": "C:/Users/<you>/.dotnet/tools/roslyn-language-server.cmd"
      }
    }
  }
}
```

If you installed with `uv tool install` (or plain pip/pipx) instead,
`roslyn-mcp` is already on PATH:

```json
{
  "mcpServers": {
    "roslyn": {
      "command": "roslyn-mcp",
      "env": {
        "ROSLYN_LSP_CMD": "C:/Users/<you>/.dotnet/tools/roslyn-language-server.cmd"
      }
    }
  }
}
```

Fallback if neither resolves on PATH in the client's spawn environment:

```json
{
  "mcpServers": {
    "roslyn": {
      "command": "python",
      "args": ["-m", "roslyn_mcp"],
      "env": {
        "ROSLYN_LSP_CMD": "C:/Users/<you>/.dotnet/tools/roslyn-language-server.cmd"
      }
    }
  }
}
```

| env var | default | purpose |
|---|---|---|
| `ROSLYN_LSP_CMD` | `roslyn-language-server` (via PATH) | full path to the `.cmd`/binary if PATH resolution fails in your client |
| `ROSLYN_MCP_ROOT` | cwd | solution/workspace root |
| `ROSLYN_READY_TIMEOUT` | 180 | max seconds `workspace_status(wait_seconds=…)` will block |
| `ROSLYN_TOOL_READY_WAIT` | 30 | seconds any semantic tool waits for project load before answering with `workspace_loading` |

Logs (Roslyn stderr + extension logs) land in `<root>/.roslyn-mcp/` — add it
to `.gitignore`.

## Tools

All positions are 1-based. Every result has a `verdict`:
`ok | workspace_loading | file_not_found | server_error | server_dead | timeout`.
An empty result with `workspace_loading` is **not** an answer — poll
`workspace_status` and retry.

| tool | what it returns |
|---|---|
| `workspace_status(wait_seconds=0)` | alive/ready/uptime; starts or restarts Roslyn |
| `document_symbols(file)` | flattened symbols with container + position |
| `definition(file,line,col)` | locations |
| `implementations(file,line,col)` | locations of implementers/overrides |
| `references(file,line,col,include_declaration,max_results)` | `total`, `by_file` |
| `hover(file,line,col)` | resolved signature/docs (markdown) |
| `diagnostics(file,min_severity)` | live per-file compiler/analyzer diagnostics, no build |
| `rename_preview(file,line,col,new_name)` | solution-wide WorkspaceEdit as per-file edit list; nothing applied |
| `refresh_file(file)` | re-sync a file the agent just edited |

## How it works / gotchas

- One Roslyn process per MCP server process, spawned lazily, kept warm.
  First `workspace_status(wait_seconds=120)` pays the project-load cost
  (`--autoLoadProjects`); everything after is fast.
- Readiness is gated on Roslyn's `workspace/projectInitializationComplete`
  notification. Before it fires, semantic queries return empty arrays that
  are indistinguishable from "no hits" — hence the verdict.
- Roslyn only answers for documents it has been sent via `didOpen`; the
  server opens files on first use and keeps them open. After editing a file
  on disk call `refresh_file` (or `diagnostics`, which refreshes implicitly).
- Server→client requests (`client/registerCapability`,
  `workspace/configuration`, …) are answered with nulls; leaving them
  unanswered stalls Roslyn.
- On Windows the `.cmd` shim is launched through the shell; point
  `ROSLYN_LSP_CMD` at it explicitly if the MCP client's PATH lacks
  `%USERPROFILE%\.dotnet\tools`.

## Dev

Using [uv](https://docs.astral.sh/uv/) (preferred):

```bash
uv sync --extra dev
uv run pytest -q
```

This creates `.venv/` and `uv.lock` (committed, for reproducible dev
installs) and installs the package editable plus `pytest`.

Without uv: `python -m venv .venv && . .venv/bin/activate` (`.venv\Scripts\activate`
on Windows), then `pip install -e ".[dev]" && pytest -q`.

Unit tests cover shaping (`shaping.py`), URI handling, and the server→client
request dispatch with a fake transport. End-to-end against a real solution
is not automated yet — see "Verify" below.

## Verify (manual, first run)

1. `cd <some .NET solution>` and run `python -m roslyn_mcp` from an MCP
   inspector, or register it in Claude Code and ask it to call
   `workspace_status(wait_seconds=120)` → expect `ready: true`.
2. `document_symbols("src/Foo/Bar.cs")` → non-empty.
3. `references` on a method in that file → `total > 0`.
