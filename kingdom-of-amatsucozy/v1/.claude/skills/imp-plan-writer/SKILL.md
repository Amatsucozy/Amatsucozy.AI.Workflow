---
name: imp-plan-writer
description: Content rules and quality bar for Amatsucozy implementation plans. Read this skill when Steward is about to write a plan. Defines step atomicity rules, verification requirements, and the mapping requirement from design doc component changes. Do not read for any other purpose.
---

# Implementation Plan Writer

Read by Steward before writing `docs/tasks/{feature}-plan.md`.  
Template location: `.amtcz/templates/implementation-plan-template.md`

---

## The mapping requirement

Every Component Change in the design doc must map to at least one plan step.  
Build the mapping explicitly before writing:

```
Component Change              → Step(s)
─────────────────────────────────────────
worker/src/retry.py (create)  → Step 1, Step 2
worker/src/main.py (modify)   → Step 3
db/migrations/ (new)          → Step 4
```

If a component has no step, the plan is incomplete.

---

## Mandatory sections

**Overview** — one paragraph: what does this plan achieve?  
**Prerequisites** — everything needed before Step 1 (libraries, feature flags, env vars)  
**Implementation Steps** — see step rules below  
**Rollback** — specific steps, not "revert the commit"  
**Definition of Done** — all conditions that must be true before ticket closes

---

## Step rules

### Atomicity
Could someone execute this step having only read this line, without making any design decisions?

Bad: "Add RetryHandler class with exponential backoff"  
Good: "Create `worker/src/retry.py`. Add class `RetryHandler` with `execute(fn, max_attempts=3, base_delay=1.0)` using `tenacity.retry(stop=stop_after_attempt(max_attempts), wait=wait_exponential(multiplier=base_delay))`."

### Verification (every step, no exceptions)

```markdown
**Verification:** [ ] pytest tests/test_retry.py::test_backoff_doubles_on_failure
```

Acceptable types: unit test name · integration test name · log line to confirm · manual step

### Sequencing
Migrations before app code. Tests alongside logic. New interfaces before implementations.

### Step template

```markdown
## Step N: {title}
**File:** `path/to/file.ext`
**Action:** {precise description}
**Verification:** [ ] {test / log / manual check}
```

---

## Quality gate

- [ ] Every Component Change maps to at least one step
- [ ] Every step names a specific file
- [ ] Every step is atomic — no design decisions required
- [ ] Every step has a verification checkbox
- [ ] Steps ordered by dependency
- [ ] No unresolved Open Questions from design doc
