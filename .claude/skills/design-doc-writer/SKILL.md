---
name: design-doc-writer
description: Governs the content rules, quality bar, and structure for Phase 1 design documents in the Amatsucozy workflow. Read this skill before drafting any design doc — it defines mandatory sections, ASCII diagram requirements, data model rules, and file naming conventions.
---

# Design Doc Writer

Defines what a Phase 1 design document must contain and how to write it well.
Read this before creating any `docs/tasks/[AMTCZ-ID]-[feature-name].md` file.

---

## Template

Always read `.amtcz/templates/task-design-template.md` before drafting.
The template defines the section order. This skill defines the quality bar for each section.

---

## Mandatory sections

Every design doc must contain all of the following. "N/A" is only acceptable if genuinely inapplicable — document why.

### Problem Statement
One to three paragraphs. Answers: what is currently broken or missing, who is affected, and what happens if this isn't fixed.

Do not frame this as a solution. "We need to add retry logic" is a solution statement. "The worker fails permanently on transient network errors, causing data loss" is a problem statement.

### Goals & Non-Goals
Two explicit lists.

Goals: specific, verifiable outcomes. "Retry transient failures up to 3 times with exponential backoff" is a goal. "Improve reliability" is not.

Non-Goals: explicit boundaries. What this ticket deliberately does not address. This prevents scope creep during implementation and review.

### Architecture / Workflow Changes
**ASCII diagram is mandatory if there is any change to flow logic.**

Not optional. Not "see architecture docs." The diagram must be inline and self-contained — someone reading only this doc must understand the flow.

The diagram must show causality and sequence, not just component names. See the diagram rules section below.

### Data Models / Schemas
**Required if any data structure changes.**

Define the actual before/after field definitions. Not "the schema will be updated" — the literal field names, types, and constraints.

```
Before:
  jobs table: id, status, created_at

After:
  jobs table: id, status, created_at, retry_count (int, default 0), last_error (text, nullable)
```

### Component Changes
List every file and module that will be modified or created. Each entry must be specific enough that the Planner can map it directly to an implementation step.

- Bad: "Update the worker"
- Good: "Modify `worker/src/main.py` — inject `RetryHandler` into `ServiceContainer` constructor"

### Open Questions
Anything that is unresolved and must be answered before or during planning. Each entry needs:
- The question
- The options being considered
- Who can answer it

Do not leave open questions implicit. If a decision was deferred, it must appear here.

### Out of Scope
Explicit list of related things this ticket does not cover. Prevents "while we're at it" scope expansion during implementation.

---

## ASCII diagram rules

The diagram must answer: given input X, what happens, in what order, through what components, producing what output?

### Required elements
- Entry point (what triggers the flow)
- Decision points (branches with labels)
- Data movement (what passes between components)
- Terminal states (success and failure paths)

### Style
Use standard ASCII box-drawing characters:
```
─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼   for boxes
→ ← ↑ ↓                  for arrows
```

Show before/after when the change modifies an existing flow:

```
BEFORE:
  Request → Worker → DB

AFTER:
  Request → Worker ──── success ──→ DB
                  │
                  └──── failure ──→ RetryHandler
                                        │
                                   ┌────┴─────┐
                                   │ attempt  │
                                   │  ≤ 3     │──→ Worker (retry)
                                   │  > 3     │──→ DeadLetterQueue
                                   └──────────┘
```

### What makes a bad diagram
- A list of components with arrows between them (component inventory, not a flow)
- Missing decision points
- Missing failure paths
- No indication of what data moves between components

---

## File naming

```
docs/tasks/[AMTCZ-ID]-[feature-name].md

Rules:
- AMTCZ-ID: assigned by ticket-id-assigner (e.g. AMTCZ-007)
- feature-name: kebab-case, descriptive, 2–4 words
- No abbreviations unless widely understood in the project

Good:   AMTCZ-007-worker-retry-logic.md
Bad:    AMTCZ-007-wrk-rtry.md
Bad:    AMTCZ-007-fix.md
Bad:    AMTCZ-007-worker-retry-logic-for-transient-network-failures-v2.md
```

---

## Context checks before writing

Before drafting, check:

1. `docs/tasks/` — are there prior tickets that modify the same files listed in Component Changes? If so, call out the potential conflict explicitly in the design doc.

2. `docs/architecture/` — is there existing architecture documentation for the components being changed? If so, the design doc must be consistent with it, or explicitly propose updating it.

---

## Quality gate (self-check before finishing)

Before marking the design doc complete, verify:

- [ ] Problem Statement describes the problem, not the solution
- [ ] Goals are specific and verifiable
- [ ] Non-Goals are explicitly listed
- [ ] ASCII diagram present (if flow changed) and shows decision points + failure paths
- [ ] Data model before/after defined (if schema changed)
- [ ] Every Component Change is file-specific, not module-vague
- [ ] Open Questions are listed with options, not just flagged as "TBD"
- [ ] Out of Scope is explicit
- [ ] Filename follows naming convention
- [ ] No conflicts with existing tickets or architecture docs (or conflicts are called out)
