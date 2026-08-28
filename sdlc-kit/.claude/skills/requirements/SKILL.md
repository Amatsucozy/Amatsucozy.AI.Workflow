---
name: requirements
description: >
  Requirements elicitation and ticket writing for the analyst role. Use at task intake — whenever the human describes work to do, reports a bug, pastes a Jira ticket, or asks for a feature. Governs the clarifying-question process, the ticket document at docs/tasks/<id>/ticket.md, and the creation of the task state file docs/tasks/<id>/main.yaml. Always use before dispatching any researcher or writing any plan.
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

## Research Mode Classification (`research` field)

Decided once at intake, alongside `workflow` — mechanical, not a feel call. Default
`full`. Set `research: pinpointed` only when ALL of these hold for EVERY AC:

- The ticket cites a row in an attached or pasted machine-generated diagnostic
  source — a SonarQube export, a SARIF table (`amtcz sarif probe`/`build` output),
  a TRX failure table (`amtcz test probe`/`run` output), a compiler error list, or
  a stack trace — that names an exact file path AND a line number or an
  unambiguous symbol.
- The source is tool output, not human recollection. "It's somewhere in
  AuthController" does not qualify; a pasted SonarQube row with `file:
  AuthController.cs, line: 142` does.
- The AC is a local fix at the cited location, not a request to understand or
  trace behavior across files — "why does X reach Y" always needs full research,
  no matter how precisely X itself is located.

One AC failing any of these downgrades the WHOLE ticket to `full` — no
partial-pinpointed tickets, and no self-assessed exceptions either: this is a
source-format check, not a confidence check, for the same reason the experience
routing in CLAUDE.md is unconditional rather than "if unsure" — a classification
that feels right from the inside is not a classification you can trust. Record the
field and move on; do not ask the human to confirm it.

`research: pinpointed` changes the shape of the researcher dispatch (see
sdlc-orchestrator SKILL.md → Workflow step 2) — it does not skip the researcher,
and it changes nothing else in the pipeline: plan/implement/verify still run in
full.

For `workflow: trivial`, this field is not evaluated (trivial bypasses research
entirely) — record `full` as the harmless unused default.

## Task State File — `docs/tasks/<id>/main.yaml`

Written at intake, in the same turn as the ticket. This is the ONLY state file
for the task: documents under the task folder carry no frontmatter — documents
are content, main.yaml is state.

```yaml
# identity — written once at intake, never edited after
id: <id>                         # lowercased Jira key, adhoc-<slug>,
                                 #   or <parent-id>-fix-<slug> for follow-ups
source: jira | user
priority: high | medium | low
workflow: full | trivial
research: full | pinpointed      # see Research Mode Classification above
follows: <parent task id>        # follow-up tasks only; omit otherwise
created: YYYY-MM-DD

# pipeline state — mutable; updated per the reporting skill
status: new | in-progress | blocked | verifying | done
phase: none | "<k> of <N>"
approved: pending | YYYY-MM-DD   # work/verification plan approval date
verified: none | zero-cost | G1 | G2 | ...
head: none | <sha of last phase-boundary commit>
```

`workflow` records the routing decision once, at intake: `full` runs every
stage; `trivial` is the single-file/obvious/reversible escape hatch. Default
`full` — downgrading to `trivial` is an explicit choice, visible and auditable
in main.yaml, never an in-flight improvisation.

Because all state transitions land in this one file, its git history IS the
pipeline timeline: `git log --oneline -- docs/tasks/<id>/main.yaml`.

## Ticket Format

Write to `docs/tasks/<id>/ticket.md`. No frontmatter — identity and state live
in main.yaml. Exactly this structure:

```markdown
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

When `research: pinpointed`, the diagnostic source's rows belong in References
verbatim (or attached), not paraphrased — the researcher's Confirm Mode dispatch
quotes them directly from here.

## Follow-Up Tasks

Work that continues a task whose pipeline already ran — a bug found after
implementation, a build broken by the change, an extension of delivered
behavior — is a NEW task, never a reopening of the old one. Full workflow,
full circle: requirements, research, plan, implement, verify. "The parent
already did research" is not a reason to skip research here.

- **Id:** `<parent-id>-fix-<slug>` (e.g. `proj-1234-fix-build-errors`).
  The slug names the problem, not a counter — a second follow-up on the same
  parent gets its own descriptive slug.
- **State:** set `follows: <parent-id>` in the follow-up's main.yaml even
  though the id encodes it — lineage is machine state, never parsed out of
  string prefixes, and it keeps chains explicit when a follow-up's parent is
  itself a follow-up.
- **Research classification is independent per task.** A follow-up whose
  parent was `pinpointed` is not automatically pinpointed — classify fresh
  from this task's own input (a fresh build-break report typically
  re-qualifies; a vaguer human-reported regression typically doesn't).
- **References:** the parent's `ticket.md`, `research.md`, and
  `final-report.md` are mandatory reference entries. Research inherits: the
  follow-up's researcher dispatch attaches the parent's map and scopes only
  the delta ("prior map attached; verify staleness and map only the failure
  area") — never a blind full re-run, never a blind reuse.
- Everything else is a normal task: same folder shape under
  `docs/tasks/<id>/`, same main.yaml lifecycle, same phase-commit markers
  (`<id>: phase N — ...` — the suffixed id keeps rollback greps from
  cross-matching the parent's commits).

## Quality Bar

- Every AC must pass the check test: you can name the command, request, or
  inspection that would prove it. If you can't, the AC is an aspiration, not a
  criterion — rewrite it.
- Condense Jira imports; never paste descriptions wholesale. The ticket is the
  distilled contract and is usually shorter than its source.
- A ticket with open questions does not advance to research. Ask, or park it.
- `research: pinpointed` requires machine-generated file/line citations for
  every AC — a ticket that merely *looks* simple still gets `full`. Ease of
  the fix and precision of the location are different questions.