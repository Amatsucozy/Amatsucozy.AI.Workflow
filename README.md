# Amatsucozy AI Workflow

A portable SDLC pipeline kit for Claude Code: a fixed set of subagents, skills,
and an output style that take a task through **requirements → research →
plan → implement → verify** with explicit human approval gates and a durable,
git-backed state file per task.

This is the successor to the AMTCZ framework — same lifecycle, fewer moving
parts. See [`sdlc-kit/MIGRATION.md`](sdlc-kit/MIGRATION.md) if you're coming
from AMTCZ.

## What's in the kit

| Piece | Role |
|---|---|
| `sdlc-orchestrator` skill | Invoked on demand; the main thread becomes the orchestrator/analyst and owns a task end-to-end |
| `researcher` agent (Haiku) | Read-only, budget-capped codebase mapping — no MCP, no writes |
| `engineer` agent (Sonnet) | Implements one approved plan phase inside an exact file scope |
| `reviewer` agent (Sonnet) | Runs build/test gates with fresh context (artifacts only, never transcripts) and returns a verdict |
| `pr-reviewer` agent | Reviews someone else's PR; produces draft comments only |
| `requirements` / `planning` / `reporting` skills | Ticket intake, work/verification plan drafting, and turn/close reporting standards |
| `run-build` / `run-test` skills | Capped, structured-report-only build and test execution (raw logs never enter context) |
| `experiences` skill | Durable lessons under `docs/experiences/`, read ambiently (see `CLAUDE.md`), written on close |
| `source-indexer` / `source-navigator` skills | Build and query a two-level context graph (`.amtcz/context.md`) so agents navigate instead of grepping cold |
| `session-eval` skill | Manual, on-request scoring of a past conversation |
| `orchestrator` output style | Condensed orchestrator rules pinned into the system prompt, for sessions where the persona drifts |

All of it lives under [`sdlc-kit/`](sdlc-kit) as a `.claude/` directory tree
you install into a target repository, plus reference docs
([`CLAUDE.md`](sdlc-kit/CLAUDE.md), [`TUNING.md`](sdlc-kit/TUNING.md),
[`MIGRATION.md`](sdlc-kit/MIGRATION.md), [`SESSION.md`](sdlc-kit/SESSION.md))
that explain the design and its open questions.

## Install

```bash
npx @amatsucozy/ai-workflow [target-dir]
```

Copies `.claude/` (and `.amtcz/` if present) into the target directory
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
3. The orchestrator scans `docs/tasks/*/main.yaml` for unfinished work, runs
   git recon, and asks whether to resume or start fresh.
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
  transcript, only diffs and artifacts — it can't inherit the implementer's
  bias.
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
