# adhoc-amtcz-mcp — Convert amtcz to an MCP server

## What & Why

`amtcz-cli/amtcz.py` was a CLI that kit skills (`run-build`, `run-test`) and
the experience-routing steps in `sdlc-kit/CLAUDE.md` invoked by shelling out
and parsing exit codes and ASCII tables. Because a shelled-out CLI carries no
machine-readable description an agent can see before calling it, its full
command/flag/exit-code contract had to live in prose — roughly 150 lines of
`CLAUDE.md`'s Reference section alone. This task converts the CLI's six
operations (`sarif build/probe`, `test run/probe`, `exp inventory/search`)
into tools on a new, independent MCP server, `amtcz-mcp`, so each tool's own
description carries that documentation. The kit's skills and `CLAUDE.md` now
call the tools directly instead of shelling out, and the Reference section
shrank from 146 to 47 lines as a result.

## How

Vendored the CLI's pure data-extraction functions (SARIF/TRX/experience
parsing) into three new modules, and reimplemented its print+logic functions
to return dataclasses (a `verdict` string plus structured data) instead of
printing an ASCII table — every distinct exit code the CLI returned maps 1:1
to a distinct `verdict` value. `amtcz-mcp` has **no dependency on
`amtcz-cli`**: the user decided during intake that since `amtcz-cli` is slated
for retirement, adding a shared dependency between the two packages just
before one is deleted would create churn for no lasting benefit — the CLI's
logic was vendored/rewritten instead of imported. The server itself uses the
official `mcp` Python SDK's `MCPServer` (note: mid-task discovery — `mcp`
2.0.0, the current stable release, renamed `FastMCP` to `MCPServer`; this is
a near drop-in rename, confirmed directly against the installed package, and
did not otherwise change the plan). Distribution is a Docker image (needed
because `sarif_build`/`test_run` shell out to `dotnet build`/`dotnet test`,
so the image bundles the .NET SDK), run over stdio — the standard pattern for
an MCP server packaged as a container. `amtcz-cli` was left functionally
untouched (zero diff on `amtcz.py`) and marked deprecated in its own README;
no CLI-fallback path exists in the rewritten docs, matching the same
"guaranteed available" certainty the old docs gave the CLI. Rejected
alternative: keep `amtcz-mcp` dependent on a refactored `amtcz-cli` — rejected
per the above retirement decision.

## Changes

- `amtcz-mcp/src/amtcz_mcp/{sarif,trx,experiences}.py` — new: vendored
  SARIF/TRX/experience-frontmatter parsing, restructured to return dataclasses
  (`SarifReport`, `SarifBuildResult`, `TrxReport`, `TestRunResult`,
  `ExpInventoryResult`, `ExpSearchResult`) with a `verdict` field replacing
  each operation's exit-code contract.
- `amtcz-mcp/src/amtcz_mcp/server.py` — new: the MCP server, registering all
  6 tools (`sarif_build`, `sarif_probe`, `test_run`, `test_probe`,
  `exp_inventory`, `exp_search`) with docstrings that are now each tool's
  sole documentation surface.
- `amtcz-mcp/Dockerfile`, `amtcz-mcp/README.md` — new: image build (Python +
  .NET SDK), stdio run instructions, `.mcp.json` registration snippet, tool
  index.
- `amtcz-mcp/pyproject.toml` — new: independent package, `mcp>=1.0` dependency
  (resolves to 2.0.0), console entry point `amtcz-mcp`.
- `amtcz-mcp/tests/**` — new: 30 pytest tests covering every verdict branch
  across all 6 tool-facing functions, with mocked `subprocess`/`shutil.which`
  so the suite needs no Docker/dotnet install to run.
- `sdlc-kit/CLAUDE.md` — routing steps 2/4 and the subagent-availability note
  now call `exp_inventory`/`exp_search` tools instead of `amtcz exp ...`
  shell commands; the "Reference — amtcz CLI" section (146 lines) replaced
  with "Reference — amtcz-mcp tools" (47 lines) — cross-tool scenario
  guidance kept, per-flag/per-verdict prose dropped since the tool
  descriptions now carry it.
- `sdlc-kit/.claude/skills/run-build/SKILL.md`,
  `sdlc-kit/.claude/skills/run-test/SKILL.md` — CLI invocations and
  exit-code tables replaced 1:1 with tool calls and verdict-string tables;
  Rules sections' substance (truncation guidance, no-raw-logs, facts-only
  reporting) left intact.
- `amtcz-cli/README.md` — 6-line deprecation note added at the top, pointing
  to `amtcz-mcp`; nothing else in the file changed.

Not changed: `amtcz-cli/amtcz.py`, `amtcz-cli/pyproject.toml` (zero diff —
confirmed at both gates), `bin/index.js`, `package.json`, and
`sdlc-kit/MIGRATION.md`/`TUNING.md`/`SESSION.md`/root `README.md` (all
explicitly out of scope per the ticket).

## Verification

**Gate G1** (after Phase 3, code-complete) — PASS. Package installs cleanly,
29/29 tests passed, all 6 tools registered correctly
(`asyncio.run(mcp.list_tools())` confirmed the exact expected name list),
`amtcz-cli/` confirmed untouched, and a manual read of all 6 tool docstrings
confirmed they're substantial enough for Phase 4 to rely on as the sole
documentation surface. Docker build was attempted but the daemon was
unreachable in the verification environment — noted as an environment
limitation, not a failure, per the pre-approved verification plan.

**Gate G2** (final, after Phase 4) — first pass PARTIAL: AC-1 through AC-5
passed with evidence (docstrings complete, verdict/exit-code mapping 1:1 for
all 6 ops with no unexplained collapses, Dockerfile+README present and
complete, zero remaining `amtcz sarif/test/exp` CLI references in the three
docs, no CLI-fallback language anywhere, `amtcz-cli/` diff confined to the
README deprecation note). AC-6 found one gap: `test_run`'s `zero_discovered`
verdict had extraction-level coverage but no wrapper-level test, unlike its
four sibling verdicts. Human approved a fix-phase (3a); engineer added
`test_run_test_zero_discovered` to `amtcz-mcp/tests/test_trx.py`, full suite
re-run at 30/30 passing. Re-confirmed AC-6 directly: all 5 `test_run` verdict
branches now have wrapper-level tests (`test_run_test_pass`, `_fail`,
`_zero_discovered`, `_no_trx`, `_dotnet_not_found`). **Final verdict: PASS,
all 6 acceptance criteria met.**

| AC | Outcome | Evidence |
|---|---|---|
| AC-1 | met | `server.py` — 6 tools, each with a docstring covering purpose/params/every verdict meaning |
| AC-2 | met | Every op's exit-code branches map 1:1 to distinct `verdict` Literal values, cross-checked against research.md |
| AC-3 | met | `Dockerfile` + `README.md` present, README covers build/run/register/tool-index; docker daemon unavailable in this environment (both gates), not a code defect |
| AC-4 | met | Zero CLI-invocation strings remain in the three docs; Reference section trimmed 146→47 lines |
| AC-5 | met | No CLI-fallback language in any rewritten doc; `amtcz-cli/README.md` carries only the deprecation note |
| AC-6 | met (after fix-phase 3a) | 30/30 tests passing, every verdict branch across all 6 operations has a corresponding test |

## Notes for Reviewers

- **Docker build is unverified end-to-end** in this environment — the CLI is
  present but no daemon was reachable at either gate. Before relying on the
  image in production, build and run it once in an environment with a
  working Docker daemon.
- **`mcp` 2.0.0's API surface differs from most existing tutorials/examples**
  (which target the 1.x `FastMCP` name) — anyone extending `server.py` should
  use `MCPServer` from `mcp.server.mcpserver`, and note `list_tools()` is
  `async def` in this version.
- The npx installer (`bin/index.js`) does not yet register `amtcz-mcp` for
  consuming repos — this was explicitly out of scope for this task (a
  deliberate, documented decision, not an oversight). A follow-up task would
  need to design how a consumer's `.mcp.json` gets the Docker-run entry
  written automatically.
- `amtcz-cli` remains fully installable and functionally unchanged — its
  actual retirement/removal is intentionally deferred to a future task, once
  `amtcz-mcp` is proven in real use.

## Post-close addendum — Docker distribution removed

After the task closed (still on this same unmerged branch/PR), the Docker
packaging decision from intake was reversed: `amtcz-mcp/Dockerfile` and
`amtcz-mcp/docker-compose.yml` were deleted, and `amtcz-mcp` now runs as a
direct Python process (console script `amtcz-mcp`, or `python -m amtcz_mcp`
via a new `__main__.py`) instead of a container.

Why: registering the Docker-based server in a client's MCP config required a
volume mount whose source path had to be supplied per-client (`$(pwd)` only
expands through a shell; a directly-spawned `docker` process gets no shell
and no substitution; VS Code's `${workspaceFolder}` doesn't generalize to
other clients) — a real, repeatedly-confusing failure mode surfaced in
practice while documenting registration. Running the server directly removes
the indirection entirely: each tool's `root` parameter already defaults to
`.`, which is simply the spawned process's own working directory — already
correct with zero configuration once a client sets its cwd to the project
root, which every mainstream MCP client already does. The .NET SDK
requirement (`sarif_build`/`test_run` shell out to `dotnet`) doesn't go away,
it just becomes an ordinary host prerequisite instead of something bundled
into an image — the same requirement `amtcz-cli` always had.

Net effect on this report's AC-3 ("ships a Dockerfile ... whose entrypoint
runs the stdio MCP server"): **no longer met as literally worded** — there is
no Dockerfile. The functional intent behind AC-3 (a documented, working way
to install and run the server) is met by the Install/Registering sections of
the current `amtcz-mcp/README.md` instead. Nothing else in this report's
Changes/Verification sections is affected — Docker was never load-bearing
for AC-1, AC-2, AC-4, AC-5, or AC-6, and the pytest suite already required no
Docker to run.
