---
name: imp-plan-writer
description: Governs the content rules, quality bar, and structure for Phase 2 implementation plans in the Amatsucozy workflow. Read this skill before drafting any implementation plan — it defines step atomicity rules, verification requirements, mandatory sections, and the mapping requirement from design doc component changes.
---

# Implementation Plan Writer

Defines what a Phase 2 implementation plan must contain and how to write it well.
Read this before creating any `docs/tasks/[AMTCZ-ID]-[feature-name]-imp-plan.md` file.

---

## Template

Always read `.amtcz/templates/implementation-plan-template.md` before drafting.
The template defines the section order. This skill defines the quality bar for each section.

---

## The mapping requirement

Every "Component Change" entry in the design doc must have at least one corresponding implementation step in the plan. No component change may be omitted.

Before writing the plan, build an explicit mapping:

```
Design doc Component Changes        →   Plan step(s)
─────────────────────────────────────────────────────
worker/src/retry.py (create)        →   Step 1, Step 2
worker/src/main.py (modify)         →   Step 3
db/migrations/ (new migration)      →   Step 4
config/schema.json (modify)         →   Step 5
tests/test_retry.py (create)        →   Step 1 (test-first)
```

If a component change does not map to any step, the plan is incomplete.

---

## Mandatory plan sections

### Overview
One paragraph. What does this plan achieve? What is the end state when all steps are complete?

### Prerequisites
Everything that must be true before Step 1 can begin:
- Libraries to install (with version pins)
- Feature flags to enable
- Environment variables to set
- External services to have running
- Branches to be on / PRs to be merged first

### Implementation steps
The core of the plan. See step rules below.

### Rollback procedure
How to undo the changes if something goes wrong after deployment. Must be specific — not "revert the commit" but the actual steps to restore the previous state including any data migrations.

### Definition of Done
The complete list of conditions that must ALL be true before the ticket is closed:
- All step checkboxes marked
- Specific tests passing
- No regressions in related test suites
- Documentation updated (if applicable)
- Code reviewed and merged

---

## Step rules

### Atomicity
Each step must be executable and verifiable independently. The test: could someone execute this step having only read this line, without needing to make any design decisions?

**Bad (requires design decisions to execute):**
> "Add RetryHandler class to worker/src/retry.py with exponential backoff"

**Good (fully specified, no decisions needed):**
> "Create `worker/src/retry.py`. Add class `RetryHandler` with method `execute(fn, max_attempts=3, base_delay=1.0)` implementing exponential backoff via `tenacity.retry(stop=stop_after_attempt(max_attempts), wait=wait_exponential(multiplier=base_delay))`. Raises `MaxRetriesExceeded` after final failure."

### Verification
Every step ends with a verification checkbox. No step is unverifiable.

Acceptable verification types:
- Unit test: `[ ] pytest tests/test_retry.py::test_backoff_doubles_on_failure`
- Integration test: `[ ] pytest tests/integration/test_worker_retry.py`
- Log check: `[ ] Confirm log line "RetryHandler: attempt 2/3" appears on transient failure`
- Manual step: `[ ] Run worker locally, introduce network failure, confirm retry behaviour in output`
- Assertion: `[ ] GET /health returns 200 after migration runs`

### Step template

```markdown
## Step N: [Short descriptive title]
**File:** `path/to/file.ext`
**Action:** [Precise description — what to add, modify, or delete, including specifics]
**Verification:** [ ] [Test name / log line / manual check]
```

### Sequencing
Steps must be ordered by dependency. The rules:
- Migrations before application code that uses the new schema
- Tests before (or alongside) the logic they test
- Infrastructure changes before services that depend on them
- New interfaces before implementations that use them

---

## File naming

```
docs/tasks/[AMTCZ-ID]-[feature-name]-imp-plan.md

The feature-name must match the design doc exactly.
Good:   AMTCZ-007-worker-retry-logic-imp-plan.md
Bad:    AMTCZ-007-imp-plan.md
Bad:    AMTCZ-007-retry-imp-plan.md  (feature name truncated)
```

---

## Open Questions check

Before writing a single step, check the design doc's Open Questions section. If any questions are unresolved:
1. Surface them to the Orchestrator
2. Do not begin planning until they are answered
3. Planning around an unresolved decision produces a hidden fork — the plan looks complete but breaks during implementation

---

## Quality gate (self-check before finishing)

- [ ] Every Component Change from the design doc maps to at least one step
- [ ] Every step names a specific file
- [ ] Every step is atomic — no design decisions required to execute it
- [ ] Every step has a concrete verification checkbox
- [ ] Steps are sequenced by dependency (migrations first, tests alongside logic)
- [ ] Prerequisites section covers all setup needed before Step 1
- [ ] Rollback procedure is specific, not generic
- [ ] Definition of Done lists all required conditions
- [ ] Filename matches the design doc's feature name exactly
- [ ] No Open Questions from the design doc are unresolved
