# Implementation Plan: [Feature Name]

**Plan ID:** [ID]
**Feature:** [Feature Name]
**Reference Design:** [Link to Technical Design Doc]
**Estimated Effort:** [Hours/Days]
**Risk Level:** [Low/Medium/High]

---

## 1. Pre-Implementation Checklist

- [ ] Reviewed Technical Design Document
- [ ] Confirmed access to required environments/secrets
- [ ] Verified current state of codebase (e.g., git pull, branch created)
- [ ] [Specific pre-condition 1]
- [ ] [Specific pre-condition 2]

---

## 2. Implementation Steps

*Break down the work into atomic, verifiable steps.*

### Step 1: [Action Name]

**Target File(s):**
*   `path/to/file.py`

**Task:**
[Description of what to do. Be specific.]

**Code Changes:**

*Option A: New File*
```python
# full content of new file
class MyNewClass:
    def __init__(self):
        pass
```

*Option B: Modification*
*   **Locate:** `def existing_function():`
*   **Change:** Add logging and error handling.

```python
def existing_function():
    # ... existing code ...
    logger.info("New logging added")  # <--- Added
    # ... existing code ...
```

**Verification:**
- [ ] Code compiles/lints without errors
- [ ] [Specific verification check, e.g., "Function returns X"]

---

### Step 2: [Action Name]

**Target File(s):**
*   `path/to/another/file.ts`

**Task:**
...

**Code Changes:**
...

**Verification:**
- [ ] ...

---

## 3. Testing Plan

### 3.1 Unit Tests
*   **File:** `tests/unit/test_feature.py`
*   **Cases:**
    *   `test_case_success`: Verify standard success path
    *   `test_case_failure`: Verify error handling

### 3.2 Integration Tests
*   **File:** `tests/integration/test_feature_flow.py`
*   **Scenario:**
    1.  Setup: Create user with X
    2.  Action: Call API Y
    3.  Assert: DB record Z is created

### 3.3 Manual Verification (Smoke Test)
1.  Start application locally (`make run`)
2.  Navigate to `http://localhost:8000/feature`
3.  Perform action X
4.  Verify log output shows "Success"

---

## 4. Deployment & Rollback

### 4.1 Deployment Steps
1.  [Database Migration Command]
2.  [Deploy Service A]
3.  [Deploy Service B]

### 4.2 Verification Post-Deploy
- [ ] Check logs for "Service Started"
- [ ] Verify specific metric/health check

### 4.3 Rollback Plan
If critical error occurs:
1.  Revert database migration: `[Command]`
2.  Rollback deployment: `kubectl rollouts undo ...`

