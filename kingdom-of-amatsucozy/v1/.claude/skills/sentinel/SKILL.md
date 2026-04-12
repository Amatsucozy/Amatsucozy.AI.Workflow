---
name: sentinel
description: Guards Amatsucozy's phase gates. Read this skill at every phase boundary — before proceeding from design to planning, planning to implementation, or when *implement is issued. Two sections: new workflow gate and resume gate. Read only the section that applies. Keep this skill loaded — it is consulted on every phase transition.
---

# Sentinel

Phase gate authority. Read the relevant section only.

---

## New workflow gate (`*sw`)

| Phase done | `--auto`? | Authority | Action |
|---|---|---|---|
| Design written | No | NONE | Stop. Summarise doc. Ask for approval. |
| Design written | Yes | YES* | Proceed to Steward immediately |
| Plan written | No | NONE | Stop. Summarise plan. Ask for approval. |
| Plan written | Yes | YES* | Proceed to Knight immediately |

*YES unless critical uncertainty exists (ambiguous requirements, irreversible decision, unresolvable external dependency). If uncertain: state "Pausing — need clarification on [X]" and stop.

**Never:** write the next phase's file as a preview. Batch phases in one response. Skip Steward.

---

## Resume gate (`*i`)

Authority to spawn Knight requires ALL of the following:
- [ ] Plan file exists at `docs/tasks/{feature}-plan.md`
- [ ] Plan has at least one unchecked step `[ ]`
- [ ] No blocker file exists at `/.amtcz/briefs/{feature}-blocker.md` (or blocker was resolved)

If blocker file exists: read it, present options to user. Do not spawn Knight until user resolves.

---

## Tool-gating

| Phase | May write | Never write |
|---|---|---|
| Design | `docs/tasks/{name}.md` | `-plan.md`, source code |
| Planning | `docs/tasks/{name}-plan.md` | source code |
| Implementation | source code, test files, plan checkboxes | new docs or plans |

---

## Status Block

Render at end of every King response:

```
**Phase:** [Design | Planning | Implementation | Idle]
**Mode:** [Manual | Auto]
**Feature:** {name or None}
**Next:** {one line}
**Context:** {one line}
```
