---
name: sentinel
description: Guards Amatsucozy's phase gates. Read this skill at every phase boundary — before proceeding from design to planning, planning to implementation, or when *implement is issued. Two sections: new workflow gate and resume gate. Read only the section that applies.
cache_control: ephemeral
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

*YES unless critical uncertainty: ambiguous requirements, irreversible decision, or unresolvable external dependency.  
If uncertain: "Pausing — need clarification on [X]" and stop.

**Never:** write the next phase's file as a preview · batch phases in one response · skip Steward.

---

## Resume gate (`*i`)

Authority to spawn Knight requires ALL:
- [ ] Plan file exists at `docs/tasks/{feature_id}-plan.md`
- [ ] Plan has at least one unchecked step `[ ]`
- [ ] No unresolved blocker at `/.amtcz/briefs/{feature_id}-blocker.md`

If blocker file exists: read it, present options to user. Do not spawn Knight until resolved.

---

## Tool-gating

| Phase | May write | Never write |
|---|---|---|
| Design | `docs/tasks/{feature_id}.md` | `-plan.md`, source code |
| Planning | `docs/tasks/{feature_id}-plan.md` | source code |
| Implementation | source code, test files, plan checkboxes | new docs or plans |
