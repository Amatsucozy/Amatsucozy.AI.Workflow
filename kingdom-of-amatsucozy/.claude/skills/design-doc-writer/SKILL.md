---
name: design-doc-writer
description: Content rules and quality bar for Amatsucozy design documents. Read this skill when King is about to write a design doc. Contains the design template, ASCII diagram rules, mandatory sections, and quality gate checklist. Do not read for any other purpose.
---

# Design Doc Writer

Read before writing `docs/tasks/{feature}.md`.

**Template:** `skills/design-doc-writer/assets/task-design-template.md` — read and fill in.  
**Diagram rules:** `skills/design-doc-writer/references/ascii-diagram-rules.md` — read if drawing a diagram.

---

## Pre-draft checks

1. Scout brief already in context? If not, King must spawn Scout first.
2. Scan `docs/tasks/` — any existing docs touching the same components? Note conflicts.
3. Scan `docs/architecture/` — any architectural constraints on components being changed? Note them.

---

## Mandatory sections

### Problem Statement
Describes the problem — not the solution.  
Bad: "We need retry logic." Good: "The worker fails permanently on transient errors, causing data loss."

### Goals & Non-Goals
Goals: specific and verifiable. Non-Goals: explicit boundary list — not optional.

### Architecture / Workflow Changes
**ASCII diagram mandatory if any flow logic changes.** Inline and self-contained.  
Read `references/ascii-diagram-rules.md` before drawing.

### Data Models / Schemas
Required if any data structure changes. Show before/after field definitions explicitly.  
"Schema will be updated" is not acceptable.

### Component Changes
Every file and module modified or created.  
Specific enough for Steward to map directly to a plan step without guessing.  
Bad: "Update the worker." Good: "Modify `worker/src/main.py` — inject `RetryHandler` into `ServiceContainer`"

### Open Questions
Each entry: the question + the options + who can answer. No implicit TBDs.

### Out of Scope
Explicit list. Prevents scope creep during Knight's execution.

---

## File naming

```
docs/tasks/{feature-name}.md
feature-name: same as feature_id (kebab-case, 2-4 words, matches checkpoint)
```

---

## Quality gate

- [ ] Problem describes the problem, not the solution
- [ ] Goals are verifiable; Non-Goals are explicit
- [ ] ASCII diagram present if flow changed — shows decisions and failure paths
- [ ] Data model before/after defined if schema changed
- [ ] Every Component Change is file-specific, not module-vague
- [ ] Open Questions list options, not just "TBD"
- [ ] Conflicts with existing docs called out explicitly
- [ ] feature-name matches feature_id from checkpoint
