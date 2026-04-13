---
name: code-implementer
description: Execution rules for Amatsucozy's Knight sub-agent. Read this skill before writing any source code. Defines test-first protocol, step completion marking, scope boundary, and when to escalate. Do not read for any other purpose.
cache_control: ephemeral
---

# Code Implementer

Read by Knight before executing any plan step.

---

## Step execution protocol

1. Read the step completely before starting
2. If verification is a test: **write the test first** — it fails, that is correct
3. Implement the change
4. Run the verification
5. On pass: mark `[ ]` → `[x]` in plan file. Move to next step.
6. On fail: see failure escalation in Knight agent definition

Never mark a checkbox before verification passes.  
Never skip a step and return to it later.

---

## Test-first rule

When verification is a unit or integration test, the test is written before the implementation. If the interface does not exist yet: create a stub, write the test against the stub, then implement.

---

## Scope boundary

The plan file is the scope boundary. Every code change must trace to a specific plan step.

When something wrong is noticed outside scope: add `# NOTE: {observation} — flagged for AMTCZ-NEXT` inline. Do not fix it. Continue.

---

## Allowed file operations

| Type | Allowed |
|---|---|
| Source code, test files | Create, modify |
| Plan file | Checkbox marking only |
| Design doc, arch docs | Read-only |
| New design or plan files | Never |

---

## Completion check

After all steps are `[x]`:
1. Verify all Definition of Done conditions in plan
2. Delete brief files for this feature from `/.amtcz/briefs/`
3. Signal King: `IMPLEMENTATION COMPLETE`
