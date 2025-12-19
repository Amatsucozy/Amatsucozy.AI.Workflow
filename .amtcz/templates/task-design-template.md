# [Task Name/ID] Technical Design

> **Status:** [Draft/In Review/Approved]
> **Date:** [YYYY-MM-DD]
> **Author:** [Name]
> **Related Issue/Story:** [Link]

---

## 1. Problem Statement

### 1.1 Context
*Describe the current functionality or system state relevant to this task.*

### 1.2 The Issue
*Describe the specific problem, bug, or limitation. Use specific examples, error logs, or user scenarios.*

### 1.3 Root Cause Analysis (Optional)
*If fixing a bug, explain WHY it is happening.*
*   **Current Behavior:** ...
*   **Technical Constraint:** ...

---

## 2. Solution Overview

### 2.1 Goals
1.  [Goal 1]
2.  [Goal 2]

### 2.2 Non-Goals
*   [What we are explicitly NOT doing]

### 2.3 Proposed Approach
*High-level summary of the solution. "We will replace X with Y by doing Z."*

---

## 3. Technical Design

### 3.1 Architecture / Workflow Changes

*Use standard ASCII diagrams to visualize the change.*

**Current Flow:**
```
[Component A] --(Old Event)--> [Component B]
```

**New Flow:**
```
[Component A] --(New Event)--> [New Component]
      |
      +--(Processed)--> [Component B]
```

### 3.2 Component Changes

| Component | Change Type | Description |
|-----------|-------------|-------------|
| `Service A` | Modify | Add validation logic to `process_X` |
| `Service B` | New | Create new `RetryHandler` class |
| `DB Schema` | Update | Add `retry_count` column to `jobs` table |

### 3.3 Data Models / Schemas
*Define any new data structures, database schema changes, or event payloads.*

**New Event: `EventName`**
```json
{
  "id": "uuid",
  "type": "event_type",
  "payload": { ... }
}
```

### 3.4 API Changes (if applicable)
*   **POST** `/api/v1/resource`
    *   **Request Body:** ...
    *   **Response:** ...

---

## 4. Implementation Strategy

### 4.1 Phasing
*   **Phase 1:** [Description]
*   **Phase 2:** [Description]

### 4.2 Risks & Mitigations
*   **Risk:** [Risk Description]
    *   **Mitigation:** [How we handle it]

### 4.3 Rollback Strategy
*   [How to revert if things go wrong]

---

## 5. References
*   [Link to existing code]
*   [Link to external documentation]

