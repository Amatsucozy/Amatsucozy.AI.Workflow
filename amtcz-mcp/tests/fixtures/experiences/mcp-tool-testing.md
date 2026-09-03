---
slug: mcp-tool-testing
use-when: Testing MCP server tools that shell out to dotnet via subprocess
domain: testing
tags: [pytest, mocking, dotnet]
symptom: subprocess.run calls hit a real dotnet install during tests
confidence: high
date: 2026-01-01
source-task: adhoc-amtcz-mcp
---

# MCP tool testing

Patch `amtcz_mcp.sarif.subprocess.run` and `amtcz_mcp.trx.subprocess.run`
(module-qualified, not the bare `subprocess` module) with
`unittest.mock.patch`, since each module does `import subprocess` at its own
top level rather than importing the function by name.
