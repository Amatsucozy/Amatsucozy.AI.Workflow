---
name: requirements
description: >
  Requirements elicitation and ticket writing for the analyst role. Use at task intake — whenever the human describes work to do, reports a bug, pastes a Jira ticket, or asks for a feature. Governs the clarifying-question process and the ticket document at docs/tasks/<id>/ticket.md. Always use before dispatching any researcher or writing any plan.
---

# Requirements & Ticket Writing

Intake is the only stage where the human is cheap to consult and misunderstanding
is cheap to fix. Every ambiguity that survives intake is paid for at 10x during
implementation. Spend the questions here.

## Elicitation

Before writing the ticket, verify you can answer all of these from what the human
said. Ask about the ones you can't — batched into one message, not a drip:

- **Observed vs expected** (bugs): what happens now, what should happen, repro
  steps or a failing example if available.
- **Scope edges**: what is explicitly out — adjacent features the human does NOT
  want touched.
- **Constraints**: backward compatibility, no new dependencies, performance
  bounds, deadline pressure that changes the quality bar.
- **Done means**: how the human personally would check it's finished. Their answer
  usually becomes AC-1 verbatim.
- **Priority conflicts**: if this collides with in-flight tasks, which wins.

Skip questions whose answers are already in the conversation or obvious from the
repo. Two or three sharp questions beat a form. If the human says "just use your
judgment", record the judgment you chose in the ticket's Constraints so it is
visible and reversible.

## Ticket Format

Write to `docs/tasks/<id>/ticket.md`, where `<id>` is the lowercased Jira key or
`adhoc-<slug>`. Exactly this structure:

```markdown
---
id: <id>
source: jira | user
priority: high | medium | low
status: new
created: YYYY-MM-DD
---

# <id> — <title>

## Problem
<1–3 sentences. What is broken/missing and where it manifests. Zero solution
language — the design stage owns the how.>

## Target
<1–3 sentences. The end state in concrete terms. WHAT is true when done.>

## Acceptance Criteria
- [ ] AC-1: <binary-checkable statement>
- [ ] AC-2: ...

## Constraints & Out of Scope
<hard limits and explicit exclusions; "none">

## References
<Jira link, related tasks, prior art; "none">
```

## Quality Bar

- Every AC must pass the check test: you can name the command, request, or
  inspection that would prove it. If you can't, the AC is an aspiration, not a
  criterion — rewrite it.
- Condense Jira imports; never paste descriptions wholesale. The ticket is the
  distilled contract and is usually shorter than its source.
- A ticket with open questions does not advance to research. Ask, or park it.
