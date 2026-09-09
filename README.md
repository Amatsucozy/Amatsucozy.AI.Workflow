# Amatsucozy AI Workflow

A portable SDLC pipeline kit for Claude Code: a fixed set of subagents and
skills that take a task through **requirements → research → plan → implement
→ verify** with explicit human approval gates and a durable, git-backed state
file per task, plus three local MCP servers that give the agents structured
build, test, database-schema, and C# semantic evidence without raw logs.

This is the successor to the AMTCZ framework — same lifecycle, fewer moving
parts. See [`sdlc-kit/MIGRATION.md`](sdlc-kit/MIGRATION.md) if you're coming
from AMTCZ.

## What's in the kit

| Piece | Role |
|---|---|
| `sdlc-orchestrator` skill | Invoked on demand; the main thread becomes the orchestrator/analyst and owns a task end-to-end |
| `researcher` agent (Haiku) | Read-only, budget-capped codebase mapping — Glob/Grep/Read plus the read-only roslyn navigation tools (`references`, `implementations`, `definition`) for tracing C# flows; no writes, no other MCP |
| `engineer` agent (Sonnet) | Implements one approved plan phase inside an exact file scope; never builds, but must run roslyn `diagnostics` on every changed `.cs` file and `references` on any changed public/internal signature before handing off |
| `reviewer` agent (Sonnet) | Runs build/test gates with fresh context (artifacts only, never transcripts) and returns a verdict; runs roslyn `diagnostics` as a prefilter so a compiler error skips the build, and uses `references`/`implementations` as evidence for caller-shaped checks |
| `pr-reviewer` agent | Reviews someone else's PR; produces draft comments only |
| `requirements` / `planning` / `reporting` skills | Ticket intake, work/verification plan drafting, and turn/close reporting standards |
| `run-build` / `run-test` skills | Capped, structured-report-only build and test execution (raw logs never enter context) |
| `experiences` skill | Durable lessons under `docs/experiences/`, read ambiently (see `CLAUDE.md`), written on close |
| `session-eval` skill | Manual, on-request scoring of a past conversation |
| `sonarqube-issues` / `sonarqube-project-map` skills | Triage SonarQube findings for the current branch or PR, and maintain the SonarQube-key ↔ repo map they read from |

All of it lives under [`sdlc-kit/`](sdlc-kit) as a `.claude/` directory tree
you install into a target repository, plus reference docs
([`CLAUDE.md`](sdlc-kit/CLAUDE.md), [`TUNING.md`](sdlc-kit/TUNING.md),
[`MIGRATION.md`](sdlc-kit/MIGRATION.md), [`SESSION.md`](sdlc-kit/SESSION.md))
that explain the design and its open questions. `CLAUDE.md` carries the
experience-first task routing and the cross-tool quick-reference tables for
the three MCP servers inline (always-on) rather than as separate skills — see
`TUNING.md` for why.

[`sdlc-kit/.devin/`](sdlc-kit/.devin) mirrors the four agents for Devin: same
prose contracts, Devin-shaped frontmatter (`allowed-tools`, Devin model ids).
The Claude and Devin agent bodies are kept identical; only the frontmatter
differs.

## MCP servers

The kit's agents lean on three stdio MCP servers, each a standalone Python
package in this repository. Register them in the target repository's
`.mcp.json` (each server's README has a `uvx` snippet pinned to the
`v1.0.0` tag that installs straight from GitHub) and the tools appear in the
agent's tool list, self-described.

| Server | Answers | Used by |
|---|---|---|
| [`amtcz-mcp`](amtcz-mcp) | "Does it build? Do tests pass? Have we hit this before?" — `sarif_build`/`sarif_probe`, `test_run`/`test_probe`, `exp_inventory`/`exp_search`. Error-only structured reports; raw build/test logs never enter context | Main thread (experience routing), `reviewer` via `run-build`/`run-test` |
| [`dbschema-mcp`](dbschema-mcp) | "What table holds X? How do I join Y to Z?" — structure from a one-time catalog snapshot, never rows. PostgreSQL and SQL Server | Main thread |
| [`roslyn-mcp`](roslyn-mcp) | "Where is this defined? Who calls it? Does this file compile?" — wraps `roslyn-language-server`; per-file `diagnostics` with no build, `references`, `implementations`, `hover`, `rename_preview`. One Roslyn process per solution, multi-repo roots supported | `researcher`, `engineer`, and `reviewer` (read-only subsets named in each agent's frontmatter), main thread |

Workers get no remote MCP — Jira, GitHub, and Confluence stay with the main
thread. The local `roslyn` server is the one exception, and a dispatch never
grants a worker an MCP tool its agent file doesn't list.

[`amtcz-cli`](amtcz-cli) is the deprecated predecessor of `amtcz-mcp`, kept
installable but no longer the documented interface.

## Install

```bash
npx @amatsucozy/ai-workflow [target-dir]
```

Copies `.claude/` into the target directory
(defaults to the current directory). Pass `--force` to overwrite an existing
install.

You can also skip the installer and copy `sdlc-kit/.claude/` into your
repository's `.claude/` directory by hand — merge rather than replace if you
already have agents/skills there.

## Using it

1. Open Claude Code in the target repository.
2. Invoke the `sdlc-orchestrator` skill (or say what you want done — the
   skill's description routes to it for ticket work, task start, or resuming
   in-flight work under `docs/tasks/`).
3. On an explicit resume/continue signal, the orchestrator scans
   `docs/tasks/*/main.yaml` for unfinished work, runs git recon, and asks
   which to resume. Otherwise it skips straight to intake.
4. Everything from there follows the workflow in
   [`sdlc-kit/.claude/skills/sdlc-orchestrator/SKILL.md`](sdlc-kit/.claude/skills/sdlc-orchestrator/SKILL.md):
   intake → research → plan (human-approved) → phase-by-phase implementation
   → gated verification → close with a PR.

Each task gets its own folder:

```
docs/tasks/<id>/
├── main.yaml             # state file: identity + pipeline state (the task's timeline via git log)
├── ticket.md             # Problem / Target / Acceptance Criteria
├── research.md           # researcher's brief
├── work-plan.md          # phased implementation plan
├── verification-plan.md  # gates and checks
└── final-report.md       # written at close; becomes the PR body
```

## Design principles

- **Delegate, don't do.** The main thread clarifies, plans, and reports; it
  rarely writes code or runs builds itself.
- **Fresh context at verification.** The reviewer never sees the engineer's
  transcript, only diffs and artifacts (including the engineer's
  Deviations/Diagnostics/Handoff sections) — it can't inherit the
  implementer's bias.
- **Semantic evidence before the compiler.** Builds are slow and concentrated
  at reviewer gates, so both engineer and reviewer run roslyn `diagnostics`
  per changed file first: an engineer output with a `.cs` change and no
  `## Diagnostics` section is an incomplete phase, and a reviewer prefilter
  that finds a `CS` error fails the gate without paying for the build.
  Per-file diagnostics are never a gate on their own — whole-solution
  verdicts still come from `sarif_build`.
- **Approval gates are real gates.** Plans and any deviation from an approved
  plan (including fix-phases after a failed gate) require explicit human
  sign-off before dispatch.
- **State lives in one place.** `main.yaml` per task, no frontmatter scattered
  across documents; its git log is the audit trail.
- **Budgets over trust.** Subagents run with hard search/output caps
  (see [`sdlc-kit/TUNING.md`](sdlc-kit/TUNING.md)) so cost stays predictable
  as pipelines scale.

## Status

`0.0.1-alpha` — the design is validated by argument, not yet by a run of real
tickets. See [`sdlc-kit/SESSION.md`](sdlc-kit/SESSION.md) for what was built,
what was cut, and the open watchpoints; see
[`sdlc-kit/TUNING.md`](sdlc-kit/TUNING.md) for every tunable constant and the
evidence that would change it.

## License

MIT
