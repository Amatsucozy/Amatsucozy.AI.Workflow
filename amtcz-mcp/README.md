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

## Registering in a consumer's MCP config

Add an entry like this to the consumer's `.mcp.json` (or Claude Code MCP
settings), pointing `command`/`args` at the same `docker run` invocation:

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
