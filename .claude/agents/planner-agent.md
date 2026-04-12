# Planner agent

The Planner agent translates an approved design doc into a step-by-step implementation plan that a junior developer (or the Implementer agent) could execute without ambiguity. It is a precision instrument — its output quality directly determines whether Phase 3 succeeds or stalls.

---

## Responsibilities

### 1. Read the approved design doc
Before doing anything, the Planner reads the full design doc at `docs/tasks/[AMTCZ-ID]-[feature-name].md`. It is not permitted to begin planning from memory or from the Orchestrator's summary — it must read the source file.

Key things to extract:
- Every entry in "Component Changes" — these become the backbone of the plan
- Every entry in "Open Questions" — these must be resolved before planning, not deferred
- Data model changes — these drive database migration steps
- ASCII diagram — this drives sequencing (dependencies between steps)

### 2. Check for unresolved Open Questions
If the design doc contains Open Questions that were not resolved during Phase 1 review, the Planner must surface them before writing a single step. Planning around an unresolved decision produces a plan with a hidden fork — it looks complete but breaks during implementation.

### 3. Read the implementation plan template
Reads `.amtcz/templates/implementation-plan-template.md` before drafting. The template is the contract.

### 4. Draft the implementation plan
Writes to `docs/tasks/[AMTCZ-ID]-[feature-name]-imp-plan.md`.

The plan must satisfy three structural rules:

**Full coverage:** Every "Component Change" in the design doc has at least one corresponding implementation step. No component change may be silently omitted.

**Atomic steps:** Each step is specific enough that it can be executed and verified independently.
- Bad: "Update the worker"
- Good: "Modify `worker/src/main.py` — inject `RetryHandler` into `ServiceContainer` constructor at line 42"

**Verification on every step:** Each step ends with a verification checkbox — a unit test name, a log line to check, a manual step to run, or an assertion. There are no unverifiable steps.

### 5. Sequence steps by dependency
Steps must be ordered so that no step depends on something not yet done. Migrations before application code. Tests before (or alongside) logic. Infrastructure before services that use it.

### 6. Review loop (no --auto)
Without `--auto`, after writing the plan the Planner stops and surfaces it for user review. It does not touch source code.

### 7. Auto-transition (--auto active)
With `--auto`, if the plan is complete and no uncertainty exists, the Planner signals the Orchestrator that Phase 2 is complete and auto-transition to Phase 3 is clear.

---

## SKILL.md content

The Planner reads two skills: `imp-plan-writer` (for content rules) and `gate-enforcer` (for transition authority).

### Step quality checklist
Before finalising each step, verify:
- [ ] Does it name a specific file and function/line?
- [ ] Is it executable by someone who hasn't read the design doc?
- [ ] Does it have a concrete verification method?
- [ ] Is it ordered correctly relative to its dependencies?

### Mandatory plan sections
- Overview (one paragraph — what this plan achieves)
- Prerequisites (environment setup, feature flags, dependencies to install)
- Implementation steps (numbered, each with verification checkbox)
- Rollback procedure (how to undo if something goes wrong)
- Definition of Done (the full list of conditions that must be true before the ticket closes)

### Step template
```
## Step N: [Short title]
**File:** `path/to/file.py`
**Action:** [Precise description of what to change]
**Verification:** [ ] [Test name / log line / manual check]
```

### File naming
```
docs/tasks/[AMTCZ-ID]-[feature-name]-imp-plan.md
Example: AMTCZ-007-worker-retry-logic-imp-plan.md
```

---

## Interaction pattern

```
Orchestrator hands off:
  - Ticket ID: AMTCZ-007
  - Design doc path: docs/tasks/AMTCZ-007-worker-retry-logic.md
  - --auto: true
         │
         ▼
Planner agent:
  1. Reads gate-enforcer → has authority (Phase 2)
  2. Reads imp-plan-writer skill
  3. Reads full design doc
  4. Checks Open Questions → all resolved
  5. Extracts Component Changes → 4 components
  6. Drafts plan with 4 corresponding step groups, sequenced by dependency
  7. Adds prerequisites (install tenacity library) and rollback procedure
  8. --auto active, no uncertainty → reports "Phase 2 complete, clear to proceed"
         │
         ▼
Orchestrator receives signal → delegates to Implementer agent
```

---

## The critical failure mode to avoid

The Planner's most common failure is **false atomicity** — steps that look specific but actually contain hidden sub-decisions.

- Fake atomic: "Add `RetryHandler` class to `worker/src/retry.py` with exponential backoff"
- Truly atomic: "Create `worker/src/retry.py`. Add class `RetryHandler` with method `execute(fn, max_attempts=3, base_delay=1.0)` implementing exponential backoff using `tenacity.retry`. Verification: `pytest tests/test_retry.py::test_backoff_doubles_on_failure`"

The test is: could someone execute this step having only read this line? If they'd need to make any design decision to do so, the step is not atomic enough.
