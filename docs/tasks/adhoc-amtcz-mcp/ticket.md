# adhoc-amtcz-mcp — Convert amtcz to an MCP server

## Problem
The kit's tooling (`amtcz-cli/amtcz.py`) is a CLI that skills (`run-build`,
`run-test`, the experience-routing steps in `CLAUDE.md`) invoke by shelling
out via Bash and parsing exit codes / ASCII tables. This works but keeps the
full command/flag/exit-code contract spelled out in prose (`CLAUDE.md`'s
Reference section) because a shelled-out CLI carries no machine-readable
description an agent can see ahead of calling it.

## Target
`amtcz`'s six operations — `sarif build`, `sarif probe`, `test run`,
`test probe`, `exp inventory`, `exp search` — are exposed as tools on a new,
independent MCP server (`amtcz-mcp`), distributed as a Docker image, running
over stdio. Each tool's own description carries the parameter/behavior/verdict
documentation an agent needs, so the kit's skills and `CLAUDE.md` can call the
tools directly and drop the CLI-flag reference prose. `amtcz-cli` stays in the
repo, functionally intact, but is no longer the kit's documented interface.

## Acceptance Criteria
- [ ] AC-1: A new `amtcz-mcp` package (independent of `amtcz-cli` — no
      dependency between them) implements an MCP server over stdio exposing
      6 tools (`sarif_build`, `sarif_probe`, `test_run`, `test_probe`,
      `exp_inventory`, `exp_search`), each with a tool description detailed
      enough to be the sole reference for an agent calling it (parameters,
      defaults, what the returned verdict field means).
- [ ] AC-2: Each tool returns structured output (not a printed ASCII table)
      that preserves every distinct verdict the CLI's exit codes 0–4
      encoded for that command (success / errors-found / no-files /
      MSBuild-level gap / dotnet-missing, etc.), plus the same underlying
      data the CLI's table carried (error/warning rows, failure rows, tag
      counts, search hits).
- [ ] AC-3: `amtcz-mcp` ships a `Dockerfile` (Python + .NET SDK, since
      `sarif_build`/`test_run` shell out to `dotnet build`/`dotnet test`)
      whose entrypoint runs the stdio MCP server; its README documents
      building the image and running it with the target repo bind-mounted
      (e.g. `docker run -i --rm -v <repo>:/workspace <image>`).
- [ ] AC-4: `sdlc-kit/.claude/skills/run-build/SKILL.md`,
      `sdlc-kit/.claude/skills/run-test/SKILL.md`, and
      `sdlc-kit/CLAUDE.md` (experience-routing steps + the `amtcz` CLI
      Reference section) are rewritten to call the `amtcz-mcp` tools by name
      instead of shelling out to the `amtcz` CLI; the Reference section is
      trimmed to what the tool descriptions don't already say (the model
      sees the live tool list once the server is registered).
- [ ] AC-5: No CLI-fallback path is documented — the rewritten docs assume
      the MCP server is available, the same certainty `CLAUDE.md` gives
      `amtcz` today. `amtcz-cli` is marked deprecated/slated for retirement
      in its own README, but not deleted.
- [ ] AC-6: A pytest suite under `amtcz-mcp` covers all 6 tool handlers
      across their distinct verdict branches (success, errors/failures
      found, no-files/no-TRX, MSBuild-level gap, zero-discovered, dotnet
      missing, no-entries-yet, no-search-flags), runnable via a documented
      command (e.g. `pytest`), and passes.

## Constraints & Out of Scope
- `amtcz-mcp` vendors its own SARIF/TRX/experience-parsing logic
  independently of `amtcz-cli` (explicit user decision) — `amtcz-cli` is
  slated for retirement once `amtcz-mcp` is proven, so no shared dependency
  is introduced between them.
- The kit's npx installer (`bin/index.js`, `package.json`'s `files` list) is
  OUT OF SCOPE — it is not updated to auto-register the MCP server in a
  consuming repo. Registration (Docker build/run, `.mcp.json` entry) is a
  manual step documented in `amtcz-mcp/README.md` only.
- `amtcz-cli` itself is not deleted or functionally changed in this task.
- Transport is stdio (not HTTP/SSE) — the Docker container is launched with
  `-i` per the standard "MCP server packaged as a Docker image" pattern.
- Non-goal: updating `sdlc-kit/MIGRATION.md`, `TUNING.md`, `SESSION.md`, or
  the top-level `README.md` beyond what AC-4/AC-5 require — flag any of
  those found stale during implementation rather than expanding scope to
  fix them silently.

## References
- `amtcz-cli/amtcz.py`, `amtcz-cli/README.md`, `amtcz-cli/pyproject.toml` —
  the CLI being converted; source of truth for the 6 operations' current
  behavior and exit-code contracts.
- `sdlc-kit/CLAUDE.md` (Experience-First Task Routing + Reference — `amtcz`
  CLI section), `sdlc-kit/.claude/skills/run-build/SKILL.md`,
  `sdlc-kit/.claude/skills/run-test/SKILL.md` — the three documents whose
  `amtcz` CLI usage this task replaces with MCP tool calls.
