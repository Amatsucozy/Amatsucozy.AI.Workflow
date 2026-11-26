---
name: requirements
description: Requirements elicitation and ticket writing at SDLC task intake — when the human describes work, reports a bug, pastes a Jira ticket, or asks for a feature. Governs the clarifying questions, docs/tasks/<id>/ticket.md, and the task state file main.yaml. Runs before any researcher dispatch or plan.
---

# Requirements & Ticket Writing

Intake is where the human is cheapest to consult and misunderstanding is
cheapest to fix. Spend the questions here.

## Elicitation

Check you can answer each of these from what the human said; ask about the
rest in one batched message:

- **Observed vs expected** (bugs): current behavior, desired behavior, repro
  steps or a failing example.
- **Scope edges**: adjacent features the human does not want touched.
- **Constraints**: compatibility, dependencies, performance, deadline
  pressure that changes the quality bar.
- **Done means**: how the human would check it's finished — usually AC-1.
- **Priority conflicts** with in-flight tasks.

Skip questions already answered by the conversation or the repo; two or three
sharp questions beat a form. If the human says "use your judgment", record the
judgment in the ticket's Constraints. A ticket with open questions does not
advance to research.

## Research Classification (`research` field)

Default `full`. Set `pinpointed` only when every AC meets all three:

- It cites a row from machine-generated diagnostics — a SonarQube export, a
  `sarif_build`/`sarif_probe` error table, a `test_run`/`test_probe` failure
  table, a compiler error list, or a stack trace — naming an exact file and a
  line or unambiguous symbol. "Somewhere in AuthController" doesn't qualify.
- The source is tool output, not recollection.
- The AC is a local fix at that location, not a question of how behavior
  flows across files.

One failing AC makes the whole ticket `full`. This is a check on the source's
format, not on how easy the fix looks; record the field without asking the
human to confirm. `pinpointed` only changes the researcher dispatch to Confirm
Mode — research, planning, implementation, and verification all still run.
For `workflow: trivial`, record `full` as the unused default.

## Task State — `docs/tasks/<id>/main.yaml`

Written at intake, in the same turn as the ticket. It is the only state file:
task documents carry no frontmatter.

```yaml
# identity — written once at intake
id: <id>                         # lowercased Jira key, adhoc-<slug>, or <parent-id>-fix-<slug>
source: jira | user
priority: high | medium | low
workflow: full | trivial
research: full | pinpointed
follows: <parent task id>        # follow-ups only
created: YYYY-MM-DD

# pipeline state — updated per the reporting skill
status: new | in-progress | blocked | verifying | done
phase: none | "<k> of <N>"
approved: pending | YYYY-MM-DD   # plan approval date
verified: none | zero-cost | G1 | G2 | ...
head: none | <sha of last phase-boundary commit>
```

`workflow` defaults to `full`; `trivial` (single-file, obvious, reversible) is
an explicit intake choice, never an in-flight downgrade. Because every
transition lands in this file, `git log --oneline -- docs/tasks/<id>/main.yaml`
is the pipeline timeline.

## Ticket — `docs/tasks/<id>/ticket.md`

```markdown
# <id> — <title>

## Problem
<1–3 sentences: what is broken or missing and where it shows. No solution language.>

## Target
<1–3 sentences: what is true when done.>

## Acceptance Criteria
- [ ] AC-1: <binary-checkable statement>

## Constraints & Out of Scope
<hard limits and explicit exclusions; "none">

## References
<Jira link, related tasks, prior art; "none">
```

- Every AC must name the command, request, or inspection that would prove it;
  otherwise rewrite it.
- Condense Jira imports — the ticket is the distilled contract and usually
  shorter than its source.
- For `pinpointed`, put the diagnostic rows in References verbatim; the
  Confirm Mode dispatch quotes them from there.

## Follow-Up Tasks

Work continuing a task whose pipeline already ran — a bug found afterwards, a
build it broke, an extension — is a new task with the full workflow. The
parent having done research is not a reason to skip it.

- **Id:** `<parent-id>-fix-<slug>`, where the slug names the problem
  (e.g. `proj-1234-fix-build-errors`).
- **State:** set `follows: <parent-id>` even though the id encodes it —
  lineage is machine state, never parsed from strings.
- **Classify research fresh** from this task's own input; a pinpointed parent
  doesn't make the follow-up pinpointed.
- **References** include the parent's `ticket.md`, `research.md`, and
  `final-report.md`. The researcher dispatch attaches the parent's map and
  maps only the delta.
- Otherwise a normal task: same folder, lifecycle, and phase-commit markers
  (the suffixed id keeps rollback greps off the parent's commits).
