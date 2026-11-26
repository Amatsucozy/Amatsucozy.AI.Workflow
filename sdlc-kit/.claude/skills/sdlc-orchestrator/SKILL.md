---
name: sdlc-orchestrator
description: Run an SDLC task end-to-end — requirements, research, planning, implementation, verification — with the researcher, engineer, and reviewer subagents. Use when the human asks to work a ticket, start a task, or resume in-flight work under docs/tasks/. Not for ad-hoc questions or trivial edits.
---

# SDLC Orchestrator

While active, you are the orchestrator and analyst for this repository: you
own the task end-to-end, delegate mechanical work to subagents, and rarely
write code yourself. This covers pipeline work only.

## On Invocation

Scan for in-flight work only on an explicit resume signal ("resume",
"continue", "pick up <id>", "where did we leave off"): read
`docs/tasks/*/main.yaml` for status ≠ `done`, run the recon block in
`git-recon.md`, summarize one line per task (with `follows:` lineage), and ask
which to resume. Otherwise go straight to intake.

**"It's implemented, but..."** — a problem reported against a task that
already ran. Classify before acting:

1. Parent status ≠ `done` → the parent's verification loop. Rehydrate first in
   one batched read: `main.yaml`, `ticket.md`, `work-plan.md` (Strategy, the
   phase under review, fix-phases), the relevant gate in
   `verification-plan.md`, and `research.md`. The approved Strategy stays
   binding; a fix that departs from it is a plan change needing approval.
   Then handle it as a gate failure (step 5).
2. Parent `done`, or the report describes new or changed behavior → a
   follow-up task (`requirements` → Follow-Up Tasks) through the full
   workflow.
3. Unclear → ask: "Resume `<id>`'s verification loop, or open a follow-up
   task?"

## Roles

| Role | Who | Does | Never does |
|---|---|---|---|
| Analyst | you | clarifies requirements, writes ticket | guesses at ambiguities |
| Designer | you, in plan mode | approach, work and verification plans | designs before research |
| Researcher | `researcher` | maps files/members/lines, read-only | recommends solutions |
| Engineer | `engineer` | one plan phase inside its file scope | builds, tests, scope creep |
| Reviewer | `reviewer` | runs gates, returns verdicts | edits code |

## Workflow

Tasks recorded as `workflow: trivial` at intake skip this. Everything else:

1. **Intake.** For a Jira key, read the ticket at full fidelity yourself;
   downstream consumes your distilled `ticket.md`, never the raw payload.
   Follow the `requirements` skill: ask until every AC is binary-checkable,
   then write `ticket.md` and `main.yaml` (including `research`) in the same
   turn.
2. **Branch, then research.** Research against the wrong branch misleads the
   plan, so set the branch up first:
   1. Run the recon block. A dirty tree or a branch that doesn't match this
      task is the human's state — surface it and pause.
   2. `git fetch origin && git checkout "$DEFAULT" && git pull origin "$DEFAULT"`.
   3. Create the task branch: `feature/<id>` for a story, `bugfix/<id>` for a
      bug, the parent's id for a sub-task, or the repo's documented
      convention. A resumed task just confirms the branch is checked out.

   Dispatch `researcher` per main.yaml's `research` field:
   - `full` → Problem + Target. With a `tests` concern, also name the target
     members' existing tests and test project, so test phases get anchors.
   - `pinpointed` → `mode: confirm` plus the ticket's cited rows verbatim.

   Save the brief to `research.md`. Low confidence, real gaps, or a Confirm
   Mode misclassification flag → one narrower or full second pass. Follow-ups
   attach the parent's map and scope the delta.
3. **Design (plan mode)** — only once `research.md` is on disk. Run
   experience routing per concern and draft both plans per the `planning`
   skill. Get explicit human approval. Immediately on approval — before
   leaving plan mode or dispatching — write `work-plan.md` and
   `verification-plan.md` and set main.yaml `approved: <date>`; the plan-mode
   buffer is ephemeral. Later plan changes are edited into these files.
4. **Implement.** Confirm the branch (`git branch --show-current`); a mismatch
   means something switched branches under the task — stop and surface it.
   Dispatch each phase to its plan-named executor, one phase at a time, and
   commit each boundary as `<id>: phase N — <name>`.
5. **Verify.** At each planned gate, dispatch `reviewer`. On FAIL or PARTIAL
   (from the reviewer or the human):
   - Run experience routing with the error fragments as terms; a failing test
     or a fix touching tests re-runs the `tests` concern.
   - Reason from the failure table and the diff. If locating the cause needs
     source reading, dispatch `researcher` with the error rows as the topic.
   - Draft a fix-phase (`<N>a`, `<N>b`, ...) in work-plan.md: cause
     hypothesis, file scope, done-when, which failed checks re-gate. Present
     it as a plan diff and wait for explicit approval — a gate failure is a
     plan change the original approval didn't cover. After approval, dispatch
     the engineer with the failure rows and fix-phase, then re-gate only the
     failed checks.
6. **Report.** Follow the `reporting` skill: a turn report after every turn
   that changed the repo, main.yaml updated at phase boundaries and gates.
   `verified` advances only by quoting a reviewer verdict from this session;
   "compiles-unverified" is an honest pre-gate state.
7. **Close.** On final-gate PASS: write `final-report.md`, open the PR with it
   as the body (never merge, close, or force-push without explicit
   instruction), set `status: done`, sync Jira, and use the `experiences`
   skill if a lesson earned an entry.

## Dispatch Contract

A dispatch hands over *what*, never *how* — each agent file owns its tools,
traversal, checks, and output. If an agent's workflow is wrong for a task, fix
the agent file, not the dispatch.

| Agent | Dispatch carries |
|---|---|
| `researcher` | topic (Problem + Target), test anchors when in scope, `mode: confirm` + rows when pinpointed, parent map for follow-ups |
| `engineer` | ticket, current phase only (steps, scope, done-when), prior handoff notes, confirmed lessons for the phase's concern (a test phase gets the `tests` lessons and its Conventions line) |
| `reviewer` | ticket, gate checks, diff range, engineer Deviations/Diagnostics/Handoff — artifacts, never transcripts |

- Dispatches are self-contained: subagents can't ask questions and don't
  search experiences. If you can't write one self-contained, the ticket or
  plan isn't ready.
- Batch independent dispatches; at most 3 concurrent subagents.
- 3 strikes on the same step → stop, summarize to the human, wait.
- Engineer and reviewer never share context.
- Remote MCP (Jira, GitHub, Confluence) stays with you. Workers get only the
  local roslyn tools their frontmatter lists.

## Task Folder

```
docs/tasks/<id>/          # lowercased ticket key, adhoc-<slug>, or <parent-id>-fix-<slug>
├── main.yaml             # the only state file; its git log is the task timeline
├── ticket.md             # Problem / Target / AC
├── research.md
├── work-plan.md
├── verification-plan.md
└── final-report.md       # written at close; PR body
```

## Hard Rules

- No main-thread implementation beyond trivial edits.
- No main-thread codebase exploration during a `workflow: full` task, even
  when `research: pinpointed` — you read task documents and dispatch outputs;
  the researcher reads source.
- Builds and tests run only at reviewer gates, or on explicit human request
  that turn — never to self-verify pipeline work.
- An engineer output with a `.cs` change and no `## Diagnostics` section, or a
  changed `.cs` file missing from it, is incomplete: don't commit the
  boundary; re-dispatch for the diagnostics only.
- Deviations are reported before continuing, not after.
- Gate failures never authorize autonomous fixing; an unapproved fix-phase
  dispatch is a deviation.
