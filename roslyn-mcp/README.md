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
| `ROSLYN_MCP_ROOT` | cwd | workspace root; may contain one repo or several (see "Multiple solutions") |
| `ROSLYN_MCP_SOLUTION` | unset | pin one `.sln`/`.slnx` (absolute or root-relative); skips discovery entirely |
| `ROSLYN_MCP_MAX_WORKSPACES` | 2 | how many Roslyn processes (one per solution) stay warm; least recently used is shut down beyond that |
| `ROSLYN_READY_TIMEOUT` | 180 | max seconds `workspace_status(wait_seconds=…)` will block |
| `ROSLYN_TOOL_READY_WAIT` | 30 | seconds any semantic tool waits for project load before answering with `workspace_loading` |

Logs (Roslyn stderr + extension logs) land in `<root>/.roslyn-mcp/<sln-stem>/`
(plain `<root>/.roslyn-mcp/` for the no-solution fallback) — add `.roslyn-mcp/`
to `.gitignore`.

## Multiple solutions (multi-repo roots)

The root may be a folder holding several repositories. Every semantic tool
maps its `file` to a solution on its own: it walks up from the file's
directory towards the root and picks the nearest directory containing
exactly one `.sln`/`.slnx`. One Roslyn process is kept per solution, so
`document_symbols("repo-b/src/X.cs")` just works — no prior
`workspace_status` call, no knowledge of which solution owns the file.

When the walk finds a directory with several solution files, or none at all
up to a root that holds some, the tool answers `verdict: workspace_unselected`
with `candidates`. Load one with `workspace_status(solution=<candidate>)`
and repeat the same call; later ambiguous files follow the most recently
selected candidate. `ROSLYN_MCP_SOLUTION` pins a single solution for the
whole session instead. A root with no solution file anywhere keeps the old
behaviour: Roslyn's `--autoLoadProjects` over the root.

`references`/`rename_preview` never cross solutions — route cross-repo
questions through `source-navigator` / `.amtcz/context.md`. Mapping a
`.csproj` to the exact `.sln` that includes it is not attempted; the
nearest-directory rule is the whole heuristic.

## Tools

All positions are 1-based. Every result has a `verdict`:
`ok | workspace_loading | workspace_unselected | file_not_found | server_error | server_dead | timeout`,
and every semantic result names the `solution` it was answered from. An
empty result with `workspace_loading` is **not** an answer — poll
`workspace_status` and retry. `workspace_unselected` carries `candidates`:
call `workspace_status(solution=<one>)`, then repeat the same call.

| tool | what it returns |
|---|---|
| `workspace_status(wait_seconds=0, solution=None)` | discovered `solutions`, every loaded workspace, alive/ready of the current one; `solution=` loads/selects one; starts or restarts Roslyn |
| `document_symbols(file)` | flattened symbols with container + position |
| `definition(file,line,col)` | locations |
| `implementations(file,line,col)` | locations of implementers/overrides |
| `references(file,line,col,include_declaration,max_results)` | `total`, `by_file` |
| `hover(file,line,col)` | resolved signature/docs (markdown) |
| `diagnostics(file,min_severity)` | live per-file compiler/analyzer diagnostics, no build |
| `rename_preview(file,line,col,new_name)` | solution-wide WorkspaceEdit as per-file edit list; nothing applied |
| `refresh_file(file)` | re-sync a file the agent just edited |

## How it works / gotchas

- One Roslyn process per *solution*, spawned lazily on the first tool call
  that touches a file of that solution, kept warm (LRU-capped by
  `ROSLYN_MCP_MAX_WORKSPACES`). The first call into each solution pays the
  project-load cost; `workspace_status(wait_seconds=120)` (or
  `workspace_status(solution=…, wait_seconds=120)`) pays it up front.
- A known solution is opened explicitly: the process is launched without
  `--autoLoadProjects` and sent the `solution/open` notification
  (`{"solution": <file uri>}`) right after `initialized` — the flow VS
  Code's C# extension uses. Verified against roslyn-language-server
  5.12.0-1.26426.8. Only the no-solution fallback still uses
  `--autoLoadProjects`.
- Readiness is gated on Roslyn's `workspace/projectInitializationComplete`
  notification, which both flows emit. Before it fires, semantic queries
  return empty arrays that are indistinguishable from "no hits" — hence the
  verdict.
- Discovery (`workspace_status.solutions`) scans at most 4 directories deep
  and skips `bin`, `obj`, `node_modules`, `.git`, `.vs`, `.roslyn-mcp`. A
  solution deeper than that is still found by the per-file walk-up, just
  not listed.
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

Unit tests cover shaping (`shaping.py`), URI handling, the server→client
request dispatch and the `solution/open` handshake with a fake transport
(`test_lsp_client.py`), solution discovery/resolution and the LRU pool
(`test_workspaces.py`), and multi-solution routing through the real tool
functions with a fake client pool (`test_server.py`). End-to-end against a
real solution is not automated — see "Verify" below.

## Verify (manual, first run)

1. `cd <some .NET solution>` and run `python -m roslyn_mcp` from an MCP
   inspector, or register it in Claude Code and ask it to call
   `workspace_status(wait_seconds=120)` → expect `ready: true`.
2. `document_symbols("src/Foo/Bar.cs")` → non-empty.
3. `references` on a method in that file → `total > 0`.
4. Multi-repo: point `ROSLYN_MCP_ROOT` at a folder holding `repo-a/A.sln`
   and `repo-b/B.sln`; `document_symbols("repo-b/src/X.cs")` → `ok` with
   `solution: repo-b/B.sln` and no `workspace_status` call first;
   `.roslyn-mcp/B/` holds that process's log.
