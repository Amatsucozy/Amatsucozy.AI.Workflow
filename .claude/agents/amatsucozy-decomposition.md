# Amatsucozy — Sub-agent & Skills Decomposition

This document describes how the Amatsucozy system prompt is broken down into composable sub-agents and skill files.

---

## Sub-agents

### 1. Orchestrator agent
The only agent the user ever talks to directly. Owns the Amatsucozy persona, routes commands, maintains the Status Block, and enforces phase gates. Thin by design — it decides *what to do* but delegates all substantive work.

→ See [orchestrator-agent.md](./orchestrator-agent.md)

### 2. Design agent
Handles Phase 1 (`*sw`). Responsible for discovery questions, writing the design doc with ASCII diagrams and explicit data model changes, and stopping for review unless `--auto` is active.

→ See [design-agent.md](./design-agent.md)

### 3. Planner agent
Handles Phase 2 (`*cip`). Reads the approved design doc and produces the `-imp-plan.md` with atomic, verifiable steps. Every component change in the design must map to an implementation step.

→ See [planner-agent.md](./planner-agent.md)

### 4. Implementer agent
Handles Phase 3 (`*implement`). Follows the plan step-by-step, writes tests first, marks steps complete as it goes. Scope boundary is the plan file — no opportunistic changes.

→ See [implementer-agent.md](./implementer-agent.md)

### 5. Doc writer agent
Handles `*create-architecture-doc` and `*create-business-doc`. These are orthogonal to the Phase 1→2→3 pipeline and run as a parallel track with their own output structures and constraints.

→ See [doc-writer-agent.md](./doc-writer-agent.md)

---

## Skills

| Skill | Consumed by | What it encodes | File |
|---|---|---|---|
| `ticket-id-assigner` | Design agent | Scans `docs/tasks/`, finds highest AMTCZ-N, assigns next unique ID | [ticket-id-assigner-SKILL.md](./ticket-id-assigner-SKILL.md) |
| `design-doc-writer` | Design agent | Design template path, ASCII diagram requirement, data model requirement, file naming rules | [design-doc-writer-SKILL.md](./design-doc-writer-SKILL.md) |
| `imp-plan-writer` | Planner agent | Implementation plan template, atomic step quality bar, verification checkbox rules, design-to-step mapping requirement | [imp-plan-writer-SKILL.md](./imp-plan-writer-SKILL.md) |
| `code-implementer` | Implementer agent | Test-first rule, step completion marking, scope boundary, blocker protocol | [code-implementer-SKILL.md](./code-implementer-SKILL.md) |
| `arch-doc-writer` | Doc writer agent | Sharded file structure (7 files), scope assessment, source investigation rules, index update | [arch-doc-writer-SKILL.md](./arch-doc-writer-SKILL.md) |
| `business-doc-writer` | Doc writer agent | Business doc structure (4 files), hard "no source code" constraint, plain language rules, index update | [business-doc-writer-SKILL.md](./business-doc-writer-SKILL.md) |
| `gate-enforcer` *(shared)* | All agents | Phase Transition Matrix, tool-gating hard rules, `--auto` flag semantics, Turn Termination Protocol | [gate-enforcer-SKILL.md](./gate-enforcer-SKILL.md) |

---

## Key design decisions

### Gate enforcer is a shared skill
The approval gate is a cross-cutting concern that all agents must respect consistently. Encoding it once in a shared skill prevents drift where one agent enforces it differently from another.

### Doc writer agent is separate from the workflow agents
`*cad` and `*cbd` are orthogonal to the Phase 1→2→3 pipeline. They don't produce design docs or imp-plans; they have their own output structures and constraints. Keeping them in a separate agent prevents the core workflow from accumulating doc-generation branching logic.

### Orchestrator is intentionally thin
If the Orchestrator absorbs logic that belongs in skills or sub-agents it becomes a god-agent. The boundary: deciding *what to do* is the Orchestrator's job. *Doing the thing* belongs in a sub-agent or skill.

### Sequential integrity even under --auto
`--auto` removes the human approval gate but does not collapse the phases. All documentation files (design doc, implementation plan) must still be generated sequentially before code is written. The flag only removes the pause-and-ask-for-approval step.

---

## File structure

```
docs/
  tasks/
    [AMTCZ-ID]-[feature-name].md           ← Phase 1 output
    [AMTCZ-ID]-[feature-name]-imp-plan.md  ← Phase 2 output
  architecture/
    README.md                              ← index, updated by arch-doc-writer
    [topic]/
      README.md
      architecture.md
      api-specification.md
      implementation-guide.md
      integration.md
      operations.md
      deployment.md
  business/
    README.md                              ← index, updated by business-doc-writer
    [topic]/
      README.md
      overview.md
      business-logic.md
      user-stories.md

.amtcz/
  templates/
    task-design-template.md
    implementation-plan-template.md
    architecture-doc-template.md
    business-doc-template.md

skills/
  gate-enforcer/
    SKILL.md
  ticket-id-assigner/
    SKILL.md
  design-doc-writer/
    SKILL.md
  imp-plan-writer/
    SKILL.md
  code-implementer/
    SKILL.md
  arch-doc-writer/
    SKILL.md
  business-doc-writer/
    SKILL.md
```
