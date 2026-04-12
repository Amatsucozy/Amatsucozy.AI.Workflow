---
name: code-implementer
description: Governs Phase 3 execution rules for the Amatsucozy workflow — test-first discipline, step completion marking, scope boundaries, and blocker protocol. Read this skill before writing any source code. Use whenever *implement is triggered or auto-transition from Phase 2 occurs.
---

# Code Implementer

Defines how to execute a Phase 2 implementation plan correctly.
Read this before touching any source code file.

---

## Pre-execution requirements

Before writing a single line of code, confirm all three:

1. **Approved plan exists** — `docs/tasks/[AMTCZ-ID]-[feature-name]-imp-plan.md` is present and complete
2. **Full plan read** — not the Orchestrator's summary, the actual file
3. **Design doc read** — `docs/tasks/[AMTCZ-ID]-[feature-name].md` for intent context

If the plan does not exist or is incomplete, do not proceed. Report to the Orchestrator.

---

## Step execution protocol

Execute steps in the exact order defined in the plan. For each step:

1. Read the entire step before starting
2. If the step has a test as verification: **write the test first** (it will fail — that's correct)
3. Implement the change specified
4. Run the verification
5. Mark the checkbox in the plan file: `[ ]` → `[x]`
6. Only then move to the next step

Never mark a checkbox before the verification passes.
Never skip a step and return to it later.

---

## Test-first rule

Where a step's verification is a unit or integration test, write the test before writing the implementation. This is a hard rule.

The test defines the contract. Writing it first:
- Confirms you understand what the step is supposed to achieve
- Catches interface mismatches before implementation
- Produces a failing test that the implementation must satisfy

If the test cannot be written before the implementation (e.g. the interface doesn't exist yet), create a stub interface first, write the test against the stub, then implement.

---

## Marking steps complete

After completing and verifying each step, update the plan file:

```markdown
Before:
**Verification:** [ ] pytest tests/test_retry.py::test_backoff_doubles_on_failure

After:
**Verification:** [x] pytest tests/test_retry.py::test_backoff_doubles_on_failure
```

This keeps the plan file as a live progress record. The user can check the plan file at any time to see exactly where implementation stands.

---

## Scope boundary

The plan file is the scope boundary. Every code change must be traceable to a specific plan step.

Do not:
- Fix unrelated bugs noticed during implementation
- Refactor code outside the plan's scope
- Add error handling not specified in the plan
- Optimise performance not specified in the plan
- Rename things for style reasons

When something genuinely wrong or improvable is noticed: note it, don't touch it, surface it to the Orchestrator for potential future ticketing. The current ticket stays clean.

---

## Blocker protocol

A blocker is anything that prevents a step from being executed as written:
- The specified file doesn't exist
- The specified interface has changed since the design was written
- A dependency is missing or at the wrong version
- The verification condition cannot be reached

When a blocker is found:

1. **Stop immediately** — do not proceed to subsequent steps
2. **Document the blocker:**
   - What the step specified
   - What was actually found
   - What information or decision is needed to unblock
3. **Report to the Orchestrator** — include the step number and blocker details
4. **Wait** — do not attempt workarounds or proceed to later steps

Proceeding past a blocker corrupts the step sequence. Later steps may depend on the blocked one.

---

## Allowed file operations in Phase 3

| File type | Allowed |
|---|---|
| Source code files | ✅ Create, modify |
| Test files | ✅ Create, modify |
| Plan file (`-imp-plan.md`) | ✅ Checkbox marking only |
| Design doc | ❌ Read-only |
| Architecture docs | ❌ Read-only |
| New design or plan docs | ❌ Forbidden |

If a change is needed that requires creating a new design or plan doc, it's a scope change — surface it as a new ticket request, don't self-initiate.

---

## Definition of Done check

After all steps are marked complete, verify the plan's Definition of Done section:

- [ ] All step checkboxes marked [x]
- [ ] Specified test suites passing
- [ ] No regressions in related test suites
- [ ] Documentation updated (if the plan specifies this)

Only when all Definition of Done conditions are met, report "Phase 3 complete" to the Orchestrator.

---

## Quality gate (self-check before reporting complete)

- [ ] Every step checkbox in the plan is marked [x]
- [ ] Every test was written before the logic it tests (or documented why not)
- [ ] No code changes exist outside the plan's step scope
- [ ] All Definition of Done conditions are met
- [ ] Any observations about adjacent issues are noted for future ticketing (not fixed)
