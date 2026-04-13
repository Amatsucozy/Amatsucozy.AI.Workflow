# {Feature Name} — Technical Design

> **Status:** Draft  
> **Date:** {YYYY-MM-DD}  
> **Author:** Amatsucozy  

---

## 1. Problem Statement

Describe the problem — not the solution. What is currently broken or missing? Who is affected? What happens if this is not fixed?

---

## 2. Goals & Non-Goals

**Goals:**
1. {Specific, verifiable outcome}
2. {Specific, verifiable outcome}

**Non-Goals:**
- {What this ticket explicitly does not address}

---

## 3. Architecture / Workflow Changes

### Current flow
```
{ASCII diagram of current state}
```

### New flow
```
{ASCII diagram of new state — show decision points and failure paths}
```

---

## 4. Data Models / Schemas

*Skip this section if no data structure changes.*

**Before:**
```
{table/schema/field definitions}
```

**After:**
```
{table/schema/field definitions — show every added, changed, or removed field}
```

---

## 5. Component Changes

| Component | Change type | Description |
|---|---|---|
| `path/to/file.py` | Modify | {What changes and why — specific enough for Steward to map to a step} |
| `path/to/new_file.py` | Create | {Purpose of the new file} |

---

## 6. Open Questions

| Question | Options | Owner |
|---|---|---|
| {Question that must be answered before or during planning} | A: … / B: … | {Who can answer} |

*Leave empty if none.*

---

## 7. Out of Scope

- {Related thing this ticket does not cover}
- {Another explicit exclusion}

---

## 8. References

- {Link to related architecture doc, existing ticket, or external doc}
