# Implementation Plan: {Feature Name}

**Feature:** {feature_id}  
**Design doc:** `docs/tasks/{feature_id}.md`  
**Risk:** Low / Medium / High  

---

## Component → Step mapping

| Component | Change type | Step(s) |
|---|---|---|
| `path/to/file.py` | Modify | Step 2 |
| `path/to/new.py` | Create | Step 1, Step 3 |

---

## Prerequisites

Before Step 1, confirm:
- [ ] {Library to install, e.g. `pip install tenacity==8.2.3`}
- [ ] {Feature flag to enable}
- [ ] {Environment variable to set}
- [ ] Branch created and up to date

---

## Implementation steps

### Step 1: {Title}

**File:** `path/to/file.ext`  
**Action:** {Precise description — what to add, modify, or delete. Specific enough that no design decisions are required to execute.}  
**Verification:** [ ] {pytest test::name | log line to confirm | manual step}

---

### Step 2: {Title}

**File:** `path/to/file.ext`  
**Action:** {Description}  
**Verification:** [ ] {check}

---

## Rollback

If deployment fails:
1. {Specific rollback step — e.g. run migration down command}
2. {Redeploy previous version command}

---

## Definition of Done

- [ ] All step verifications pass
- [ ] No regressions in `{related test suite}`
- [ ] {Any other required condition}
