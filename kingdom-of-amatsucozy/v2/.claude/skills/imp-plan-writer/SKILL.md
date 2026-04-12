---
name: imp-plan-writer
description: Content rules and quality bar for Amatsucozy implementation plans. Read this skill when Steward is about to write a plan. Contains the plan template, step atomicity rules, verification requirements, and the mapping requirement from design doc component changes. Do not read for any other purpose.
---

# Implementation Plan Writer

Read by Steward before writing `docs/tasks/{feature_id}-plan.md`.

**Template:** `skills/imp-plan-writer/assets/implementation-plan-template.md` — read and fill in.

---

## The mapping requirement

Every Component Change row in the design doc must map to at least one plan step.  
Build the mapping table (Section 1 of the template) before writing any steps.

If a component has no corresponding step, the plan is incomplete — do not proceed.

---

## Step rules

### Atomicity

Could someone execute this step having only read this line, without making any design decision?

Bad: "Add RetryHandler with exponential backoff"  
Good: "Create `worker/src/retry.py`. Add class `RetryHandler` with `execute(fn, max_attempts=3, base_delay=1.0)` using `tenacity.retry(stop=stop_after_attempt(max_attempts), wait=wait_exponential(multiplier=base_delay))`. Raises `MaxRetriesExceeded` after final failure."

### Verification — every step, no exceptions

```markdown
**Verification:** [ ] pytest tests/test_retry.py::test_backoff_doubles
```

Acceptable: unit test name · integration test name · specific log line · explicit manual step.  
"Check it works" is not acceptable.

### Sequencing

- Database migrations before application code that uses the new schema
- Tests alongside the logic they verify (test-first: written before the logic)
- New interfaces before implementations that depend on them

---

## Conflict handling

If impact brief verdict is `CONFLICTS FOUND`:
- Write conflict summary as the first section of the plan
- Do not write implementation steps
- Signal King: `CONFLICTS FOUND — awaiting user input`

If verdict is `INDEX INCOMPLETE`:
- Note unindexed files in the plan preamble
- Continue writing steps — unindexed files can still be planned

---

## Quality gate

- [ ] Component → Step mapping table complete — no silent omissions
- [ ] Every step names a specific file
- [ ] Every step is atomic — no design decisions required
- [ ] Every step has a concrete verification checkbox
- [ ] Steps ordered by dependency
- [ ] No unresolved Open Questions from design doc
- [ ] Rollback procedure is specific (not "revert the commit")
- [ ] Definition of Done lists all required conditions
