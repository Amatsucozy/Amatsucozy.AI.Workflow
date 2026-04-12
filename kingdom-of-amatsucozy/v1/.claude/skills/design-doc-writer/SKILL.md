---
name: design-doc-writer
description: Content rules and quality bar for Amatsucozy design documents. Read this skill when King is about to write a design doc. Defines mandatory sections, ASCII diagram requirements, data model rules, and the quality gate checklist. Do not read for any other purpose.
---

# Design Doc Writer

Read before writing `docs/tasks/{feature}.md`.  
Template location: `.amtcz/templates/task-design-template.md`

---

## Pre-draft checks

1. Scan `docs/tasks/` — any existing docs touching the same components? Note conflicts.
2. Scan `docs/architecture/` — any architectural constraints on components being changed? Note them.
3. Scout brief already read? If not, prompt King to spawn Scout first.

---

## Mandatory sections

### Problem Statement
Describes the problem — not the solution. One sentence minimum.  
Bad: "We need retry logic." Good: "The worker fails permanently on transient errors, causing data loss."

### Goals & Non-Goals
Goals: specific, verifiable. Non-Goals: explicit boundary list.

### Architecture / Workflow Changes
**ASCII diagram mandatory if any flow logic changes.** Inline, self-contained.  
For diagram rules → read `skills/design-doc-writer/references/ascii-diagram-rules.md`

### Data Models / Schemas
Required if any data structure changes. Show before/after field definitions — not "schema will be updated."

### Component Changes
Every file and module modified or created. Specific enough for Steward to map directly to a step.  
Bad: "Update the worker." Good: "Modify `worker/src/main.py` — inject `RetryHandler` into `ServiceContainer`"

### Open Questions
Each entry: the question + the options + who can answer. No implicit TBDs.

### Out of Scope
Explicit list. Prevents scope creep during implementation.

---

## File naming

```
docs/tasks/{feature-name}.md
feature-name: kebab-case, 2-4 words
```

---

## Quality gate (check before marking done)

- [ ] Problem describes the problem, not the solution
- [ ] Goals are verifiable; Non-Goals are explicit
- [ ] ASCII diagram present if flow changed — shows decisions and failure paths
- [ ] Data model before/after defined if schema changed
- [ ] Every Component Change is file-specific
- [ ] Open Questions list options, not just "TBD"
- [ ] Conflicts with existing docs called out explicitly
