---
slug: mcp-python-sdk-fastmcp-renamed-mcpserver
use-when: "use when building or debugging a Python MCP server against the official `mcp` PyPI package and either FastMCP import fails or tool-listing/introspection code doesn't work as documented"
domain: process
tags: [mcp, python, fastmcp, breaking-change, sdk-version]
symptom: "ModuleNotFoundError: No module named 'mcp.server.fastmcp'"
confidence: observed-once
date: 2026-08-24
source-task: adhoc-amtcz-mcp
---

# `mcp` 2.0.0 renamed FastMCP to MCPServer and made list_tools() async

## Situation
Building `amtcz-mcp`, a new stdio MCP server, an engineer dispatch followed
widely-documented sample code (`from mcp.server.fastmcp import FastMCP`,
`@mcp.tool()`, `mcp.run(transport="stdio")`) and got blocked immediately:
`FastMCP` doesn't exist anywhere in the installed `mcp` package.

## Lesson
The official `mcp` Python SDK (PyPI: `mcp`, homepage modelcontextprotocol.io)
released a genuine breaking major version, 2.0.0, that renamed and moved the
high-level decorator-based server class: `mcp.server.fastmcp.FastMCP` →
`mcp.server.mcpserver.MCPServer`. The migration is a near drop-in rename for
the common path — same `MCPServer(name)` constructor, same `@mcp.tool()`
decorator syntax (decorated functions stay directly callable as plain
Python), same `mcp.run(transport="stdio")` — but one behavior changed
silently: `list_tools()` became `async def` (was effectively synchronous
usage in FastMCP-era examples). Any introspection code needs
`asyncio.run(mcp.list_tools())`, not a bare call. Before writing server code
against this package, check the installed version
(`pip show mcp` / `importlib.metadata.version("mcp")`) — if it's `>=2.0`,
use `MCPServer`, not `FastMCP`, and treat `list_tools()` as async.

## Evidence
`amtcz-mcp` Phase 2 (this task): dispatched engineer wrote `server.py`
against `FastMCP`, `pip install -e amtcz-mcp` resolved `mcp==2.0.0` (the
current stable release; `pip index versions mcp` shows the version line runs
...1.28.1, 1.29.0, 2.0.0 — a real major bump, not a typo/name collision).
Orchestrator verified directly: `mcp.server.mcpserver.MCPServer` exists with
matching `__init__`/`.tool()`/`.run()` signatures to the old `FastMCP`;
`inspect.getsource(MCPServer.list_tools)` confirmed `async def`. Fixed by
swapping the import and using `asyncio.run(...)` for introspection — no other
code changes needed. Re-verified working: `amtcz-mcp/src/amtcz_mcp/server.py`,
commit `0f2380e`.

## Applies When / Not When
Applies to any NEW Python MCP server built against a freshly-resolved `mcp`
dependency (unpinned or `>=1.0`-style specs will pick up 2.0+ going forward).
Does not apply to existing code already pinned to `mcp<2.0` — that code keeps
working with `FastMCP` until/unless the pin is lifted. Does not cover the
HTTP/SSE transport paths or auth-related APIs, which were not exercised by
this task's stdio-only server — those may have additional 2.0 changes beyond
what's confirmed here.
