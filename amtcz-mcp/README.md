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

## Building the image

From the repo root, using `amtcz-mcp/` as the build context:

```
docker build -t amtcz-mcp amtcz-mcp/
```

## Running it

The server speaks MCP over stdio, so it must be run with stdin/stdout
attached (`-i`) and the target repo mounted at `/workspace` (the tools'
`root` parameter defaults to `.`, i.e. the container's working directory):

```
docker run -i --rm -v "$(pwd):/workspace" amtcz-mcp
```

## Using Docker Compose

`docker-compose.yml` is a convenience for local development and manual
testing — building and running the server without retyping the `docker`
invocation above. It is not what an MCP client uses at call time (clients
spawn the server directly per their `.mcp.json` entry, below); use it when
you're iterating on `amtcz-mcp` itself or poking at it by hand.

```
docker compose build
docker compose run --rm -T amtcz-mcp
```

`-T` disables pseudo-TTY allocation — required, since the server speaks raw
newline-delimited JSON over stdio and a TTY would interfere with that
framing (same reason plain `docker run` above uses `-i` without `-t`).

By default the compose service mounts the repo root (one level up from
`amtcz-mcp/`) at `/workspace`, so `docker compose run --rm -T amtcz-mcp`
works out of the box against this kit's own repo. To point it at a different
target repo, override `WORKSPACE`:

```
WORKSPACE=/path/to/other/repo docker compose run --rm -T amtcz-mcp
```

## Registering in a consumer's MCP config

**Important:** the `$(pwd)` used in the plain shell command above only works
when Docker is invoked *through a shell*. An MCP client spawns `docker`
directly (no shell in between), so `$(pwd)` — or any other shell syntax —
gets passed to Docker as a literal string, not expanded, and Docker will
reject it (`invalid characters for a local volume name`). In a JSON config,
the `-v` source must be either a path token your specific client substitutes
for you, or a hardcoded absolute path — never `$(pwd)`.

- **VS Code's `mcp.json`** (`{"servers": {...}, "type": "stdio", ...}`
  schema) substitutes `${workspaceFolder}` for you — use it as shown below.
- **Every other client** (Claude Desktop, Claude Code's `.mcp.json`, etc.)
  performs no substitution at all — replace `${workspaceFolder}` with a
  hardcoded absolute path to the target repo instead.

```json
{
  "mcpServers": {
    "amtcz": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "${workspaceFolder}:/workspace",
        "amtcz-mcp"
      ]
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

To iterate on the server without Docker, install it editable from inside
`amtcz-mcp/`:

```
pip install -e ".[dev]"
```
