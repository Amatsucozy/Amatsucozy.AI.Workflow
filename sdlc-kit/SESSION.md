# Session Summary: AMTCZ → SDLC Kit

## The Arc

We started with document templates and ended with a complete successor framework to your AMTCZ system — but the more interesting story is how many pieces were built, challenged, and rebuilt or killed along the way. Roughly half the session's value came from *removals*.

## What Was Built (chronological)

1. **Five communication templates** (ticket, investigation, work plan, verification plan, final report) → packaged as the `amtcz-comms` skill — still valid standalone for your AMTCZ repos.
2. **code-researcher agent** — Haiku, read-only, budget-capped, no MCP.
3. **SDLC structure decision** — roles mapped to agent boundaries by isolation criteria (context flooding, tool permissions, verification independence), not org-chart symmetry: analyst/designer stay in the main thread, researcher/engineer/reviewer become subagents.
4. **The kit itself** — orchestrator, agents, skills, hooks, then declared AMTCZ's successor with MIGRATION.md and the experiences layer, MCP liaisons, and context-graph integration carried over.
5. **Hardening round** — Stop/PreToolUse hooks, telemetry, TUNING.md calibration register, output style, dispatch checklist (self-graded 7.5 → 8).
6. **Efficiency round** (your cache/RPM pushback) — gather-then-act batching, output caps, fatter phases, two-tier reports.
7. **Late additions** — pr-reviewer, git-recon reference, run-build/run-test, plan persistence on approval, experience attachment to dispatches.

## What Was Transformed (the killings and conversions)

| Piece | Journey | Why |
|---|---|---|
| Jira/GitHub liaisons | agents → **deleted**, MCP on main thread | platform now defers tool definitions; condensing tickets before the analyst was lossy exactly where fidelity mattered |
| All hooks | built + tested → **removed** on your usage evidence | no observed value; secret protection survived as declarative `permissions.deny` |
| Orchestrator | CLAUDE.md → **on-demand skill** | invocable, no conflicts with your other agents |
| Loop reports | files → **inline tables** + ticket frontmatter + git | token cost; durable state = git + 4 frontmatter fields |
| Experiences | one skill → **split**: reader in CLAUDE.md (commanding, two-stage routing: semantic search → `use-when` confirmation), writer as skill | retrieval must be reflexive and universal; writing is deliberate |
| Builder/tester | request → agents → **skills** (run-build/run-test) | output contract already fit in a table; agents added ~40k bootstrap per gate to protect against 60 capped lines |
| Reviewer | executor → pure judge → **executor again** (Sonnet, uses the skills) | followed the builder/tester journey; regained self-contained verdicts |

## Final State

**4 agents** (researcher-Haiku, engineer-Sonnet, reviewer-Sonnet, pr-reviewer), **7 skills + git-recon**, CLAUDE.md experience routing, settings.json, TUNING.md, MIGRATION.md. State lives in exactly three places: git, ticket frontmatter, task documents.

## The Principles That Emerged

1. **Boundaries need nameable isolation reasons** — this test killed two agents and converted two more.
2. **Contracts vs judgment**: enforce mechanically only after instructions demonstrably erode (hooks retired; deny rules stayed).
3. **Platform constraints expire** — the liaison retirement and my stale "subagents can't nest" claim (lifted in v2.1.172, caught by search) are the same lesson.
4. **Retire with reversal signals** — TUNING.md records every guess and every removal with the evidence that would bring it back.
5. **Verify edits by grepping for the new text** — two silent `.replace()` failures bit us; asserts and grep-verification became standard.

## Honest Status

The design is validated by argument, not by tickets — still an unvalidated ~8/10. Known watchpoints: orchestrator trigger reliability (single point of failure now), specialist executors respecting in-prompt contracts, reviewer actually using the capped pipelines, phase sizing. Everything on that list resolves the same way: run five real tickets, read the evidence, and let TUNING.md do its job.