---
slug: amtcz-mcp-server-package-convention
use-when: "use when adding a new Python MCP server package to this repo, or reviewing whether one conforms to the amtcz-mcp house convention"
domain: process
tags: [mcp, python, convention, packaging, tool-design]
symptom: "new MCP server package works but doesn't match amtcz-mcp's layout, tool naming, or verdict docs"
confidence: observed-once
date: 2026-09-04
source-task: adhoc-dbschema-mcp-review
---

# The amtcz-mcp convention is a checklist, and the two easiest items to skip are the ones that bite

## Situation
`dbschema-mcp` was added as the repo's second MCP server. It worked — 7 tools
registered, all verdicts correct — but had drifted from the convention
`amtcz-mcp` established, in ways that only surface later: at `git add` time,
at tool-collision time, and when an agent has to decide what to do about a
verdict it just received.

## Lesson
A new Python MCP server in this repo conforms when it has all of: `src/<pkg>/`
layout with `server.py` + pure logic modules + `__main__.py` + `__init__.py`
docstring; `pyproject.toml` with setuptools, `requires-python >=3.10`,
`mcp>=1.0`, `[project.scripts]` entry point, `license`/`authors`/`keywords`;
`from mcp.server.mcpserver import MCPServer` (see
`mcp-python-sdk-fastmcp-renamed-mcpserver`); every tool returning a plain
JSON-serialisable dict carrying `verdict`; a `verdict meanings:` docstring
block that says what the agent should **do** about each value, not just name
it; cross-tool preference guidance in each docstring ("prefer X over Y
when…"); `<domain>_<verb>` tool names so related tools group and generic verbs
don't collide with other servers' tools in a shared list; committed
`.gitignore`, `uv.lock`, `.mcp.json.example`, and a `CLAUDE.md.example`
routing block for cross-tool judgment; and `tests/test_server.py` pinning the
exact registered tool-name list plus the plain-dict contract. The two skipped
most often are `.gitignore` (this repo has **no root `.gitignore`**, so a
package without its own will commit `.venv/` the moment anyone runs the tests)
and `test_server.py` — which is not ceremony: writing it is what caught a real
stale-cache bug that six passing unit tests had missed.

## Evidence
`dbschema-mcp` review, this task. Missing `.gitignore` was proven concrete —
running `uv run pytest` created a 36-package `.venv/` inside an untracked
directory with nothing to exclude it. Adding the convention's
`tests/test_server.py` immediately failed two assertions, one of which was a
genuine defect (see `mcp-forced-reload-must-fail-closed`). Tool descriptions
grew 264–624ch → 598–1247ch once the terse `verdict: "ok" | "no_match"`
one-liners were rewritten as `verdict meanings:` blocks. Final state: 44 tests
passing, `git add -An` staging exactly the 20 intended files. Reference
implementation to copy from: `amtcz-mcp/` (`server.py`, `.gitignore`,
`.mcp.json.example`, `tests/test_server.py`) and the "Reference — amtcz-mcp
tools" block in `sdlc-kit/CLAUDE.md`.

## Applies When / Not When
Applies to Python MCP servers living as sibling packages in this repo, which
are consumed by agents over stdio and registered alongside each other. The
`<domain>_<verb>` naming rule matters specifically because tools from several
servers share one flat namespace in the agent's tool list — it is not a style
preference and does not apply to a server that will ever be the only one
registered. Does not cover HTTP/SSE transports, auth, or MCP resources and
prompts; every server here is stdio + tools-only so far.
