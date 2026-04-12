---
name: ticket-id-assigner
description: Assigns the next unique AMTCZ-N ticket ID for a new workflow. Use this skill whenever *start-workflow is triggered and a new ticket needs to be created. Read this before assigning any ticket ID — never guess or derive the next ID from memory.
---

# Ticket ID Assigner

Assigns a unique, sequential `AMTCZ-[N]` ticket ID for a new development task.
Always run this before creating a design doc.

---

## Assignment process

1. List all files in `docs/tasks/`
2. Extract ticket numbers from filenames matching the pattern `AMTCZ-[0-9]+`
3. Find the highest existing number
4. Assign `AMTCZ-[highest + 1]`, zero-padded to 3 digits

If `docs/tasks/` is empty or does not exist, assign `AMTCZ-001`.

---

## ID format

```
AMTCZ-001
AMTCZ-002
...
AMTCZ-010
AMTCZ-011
```

Always zero-pad to 3 digits. If the project grows beyond 999 tickets, extend to 4 digits (`AMTCZ-1000`) — do not truncate.

---

## Uniqueness rule

The ID must be unique across ALL files in `docs/tasks/`, including:
- Design docs: `AMTCZ-007-worker-retry-logic.md`
- Implementation plans: `AMTCZ-007-worker-retry-logic-imp-plan.md`

Both files share the same ticket ID. The number is assigned once and never reused, even if a ticket is abandoned or deleted.

---

## Examples

```
docs/tasks/ contains:
  AMTCZ-001-auth-jwt.md
  AMTCZ-001-auth-jwt-imp-plan.md
  AMTCZ-003-db-migration.md
  AMTCZ-005-retry-logic.md
  AMTCZ-005-retry-logic-imp-plan.md

Highest found: 5
Next ID: AMTCZ-006
```

Note: gaps in the sequence (002, 004 missing above) are fine. The rule is highest-found + 1, not fill-the-gap.

---

## Output

Return the assigned ID as a string: `AMTCZ-006`

Pass this to the Design agent as part of its handoff context. The Design agent uses it to construct the filename and populate the ticket header in the doc.
