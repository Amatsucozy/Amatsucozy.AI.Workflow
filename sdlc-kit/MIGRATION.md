# Migrating from AMTCZ

This kit is AMTCZ's successor: same lifecycle (design → plan → implement →
verify), fewer moving parts, and the mechanisms that proved themselves carried
forward. This file maps old to new and states what changed and why.

## Role Mapping

| AMTCZ | Successor | Change |
|---|---|---|
| King (orchestrator) | **Main thread** via the `sdlc-orchestrator` skill (invoked on demand) | The main thread IS the orchestrator while the skill is active — no standing persona, so it cannot conflict with other agent setups in the same repo. Also absorbs the analyst role (requirements skill), since elicitation needs the human dialogue only the main thread has. |
| Scout (investigation) | `researcher` subagent | Same job, now explicitly Haiku with hard search budgets (3 Glob + 8 Grep) and a fixed traversal order (context graph → glob → grep → read). |
| Steward (planning) | `planning` skill, main thread | Demoted from agent to skill — planning is judgment the human negotiates in plan mode, so a subagent handoff only added a lossy boundary. |
| Knight (implementation) | `engineer` subagent | 3-strike escalation kept. New: hard no-build rule (verification decoupled), scope-as-fence, mandatory Deviations section. |
| Chancellor (post-exec audit) + Sentinel | `reviewer` subagent | Merged. Key upgrade: guaranteed fresh context — receives artifacts only, never transcripts, so it can't inherit the implementer's bias. |
| Scoped MCP subagents (GitHub, Jira) | **Retired** — MCP attaches to the main thread | The quarantine pattern solved eager tool-definition loading, which Claude Code now defers by default (definitions load on demand via tool search). Liaison hops also condensed Jira tickets before the analyst saw them — lossy exactly where fidelity matters most. The payload discipline survives as the MCP Usage rules in the sdlc-orchestrator skill. |
| Experience layer (docs/experiences/) | `experiences` skill | Format kept (slug + semantic frontmatter). New: mandatory read-path citation in plan Strategy, write-path quality bar, observed-once → proven lifecycle. |
| amtcz-comms document templates | Inlined into each role's prompt/skill | Formats live where they're consumed — no separate skill trigger needed. Field names and section semantics preserved (Problem/Target/AC, phases, gates, Deviations). |
| Checkpoint resume | Phase-boundary commits + SessionStart hook | Upgraded from instruction to enforcement: the hook injects in-flight tasks deterministically before the first message. |

## What the Successor Fixes

1. **Fan-out RPM spikes** — hard cap of 3 concurrent subagents; `parallel-ok`
   only for disjoint-scope phases; one-phase-at-a-time engineer dispatch.
2. **Context cost of MCP** — tool definitions are deferred by the platform;
   raw payloads are contained by MCP Usage rules (full-fidelity reads only at
   intake, ~5-line log excerpts, distilled ticket.md for everything
   downstream). Worker subagents carry no MCP at all.
3. **Verification cost** — build/test rights concentrated in the reviewer,
   batched into a default two-gate schedule; engineers structurally cannot
   trigger expensive builds.
4. **Silent drift** — Deviations reporting required at three layers (engineer
   output, reviewer scope-drift findings, orchestrator loop reports).
5. **Startup amnesia** — the orchestrator skill's On Invocation protocol checks
   docs/tasks/ and derives the change view from git before taking work.
   (SessionStart/Stop hooks were tried and retired — no observed value.)
6. **Legibility** — SDLC role names; a colleague understands the structure
   without the AMTCZ glossary.

## Migration Steps

1. Unzip into the repo root (or merge `.claude/` if one exists).
2. Move `docs/experiences/` over unchanged; add missing frontmatter fields
   (`symptom`, `confidence`) opportunistically as entries get touched.
3. Attach your Jira/GitHub MCP declarations at project scope so the main
   thread can use them (e.g. `.mcp.json`); do not attach any MCP server to the
   worker subagents.
4. Install `source-navigator` / `source-indexer` skills where subagents can see
   them (project `.claude/skills/` or `~/.claude/skills/`).
5. In-flight AMTCZ tasks: finish them under the old system; start new tasks
   here. The docs/tasks layout is compatible enough that the SessionStart hook
   will surface both.
6. Retire agent files for King/Scout/Steward/Knight/Chancellor/Sentinel once no
   in-flight task references them.

## Deliberately Not Carried Over

- **Adversarial debate workflows** — experimental in AMTCZ; add later as an
  optional skill if the reviewer's fresh-context audit proves insufficient.
- **opusplan-style plan/execute model toggling** — the cache-write inflation
  cost more than the quality gain; the successor uses fixed per-role models.
- **Formal scoring/consolidation (v1–v3 plans)** — replaced by the simpler
  observed-once → proven promotion in the experiences skill.
