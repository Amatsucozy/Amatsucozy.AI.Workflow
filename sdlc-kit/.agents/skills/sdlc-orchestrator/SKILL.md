---
name: sdlc-orchestrator
description: Run or resume an SDLC task through requirements, research, planning, implementation, and independent verification using researcher, engineer, and reviewer agents. Use for end-to-end ticket work or explicit pipeline requests, not ad-hoc questions or trivial edits.
---

# SDLC Orchestrator

Own the invoked pipeline task end-to-end. Delegate source exploration,
implementation, and independent verification to the kit's Codex agents.
Keep this workflow scoped to the invoked task.

## Codex Setup

Use `researcher`, `engineer`, and `reviewer` from `.codex/agents/` in the
project or the installed personal agent directory. They inherit the session's
model and reasoning effort. Follow their Input and Output Contracts.
Use available Codex agent tools; do not invent tool names or model mappings.
If delegation or a required role is unavailable, report that dependency before
starting work that requires it. Never claim a main-thread check is an
independent reviewer verdict.

Read companion skills from the installed skill listing, or the sibling
`../<skill-name>/SKILL.md` in this kit. Use available shell/file tools for
local work and discover configured MCP tools before calling them. Project
instructions come from applicable AGENTS.md files. The workflow below does
not depend on a separate always-loaded project reference.

User instructions and existing authorization take precedence over the
workflow's approval conventions. Do not ask again for already-authorized
work. A planning tool tracks progress; it is not an approval mechanism and
cannot switch the session into Plan mode. Write reviewable plans to disk
before requesting any approval that is still needed.

## On Invocation

On an explicit resume signal, read `docs/tasks/*/main.yaml` for unfinished
tasks and run [git-recon.md](git-recon.md). Show task state and `follows`
lineage; resume the named task, or the single unambiguous match. Ask which
only when there are multiple plausible tasks. A new ticket goes to intake
without a resume scan.

For a problem reported against prior work:

- If the parent never passed its final gate and the planned behavior is
  failing, resume its verification loop. Read main.yaml, ticket.md,
  research.md, the current work-plan phase and fixes, and the relevant
  verification gate together before routing the failure. Preserve Strategy.
- If the parent is done or behavior is newly requested, create a follow-up
  through `requirements`; inherit the parent's research as a map to verify
  and extend, not as proof that fresh research is unnecessary.
- Ask one focused question only if the task or intended behavior is unclear.

## Roles

| Role | Executor | Responsibility | Boundary |
|---|---|---|---|
| Analyst | main thread | requirements and ticket | resolve material ambiguity |
| Designer | main thread | paired plans after research | no premature design |
| Researcher | researcher | file/member/line maps, read-only | no solution design |
| Engineer | engineer | one scoped phase and C# diagnostics | no builds or tests |
| Reviewer | reviewer | independent gates and AC evidence | no code edits |

## Experience Routing

After intake establishes the problem, discover and call `exp_inventory`,
then derive search terms from its tags and the task's error fragments.
Route each concern separately: `implementation` always, and `tests`
whenever the work adds, changes, or fixes tests — derive test-framework,
fixture, and assertion terms for it and run its own `exp_search`; a single
search on the implementation problem retrieves no test lessons.
Use `exp_search` with relevant tag, symptom, and keyword parameters from its
schema. Confirm candidates against `use-when`, then read only matches.
If those tools are unavailable, use `rg` over `docs/experiences/` frontmatter
and read matching entries. No directory or no confirmed entries means no
experience match. Cite matched or deliberately overridden slugs in Strategy
per concern; a plan with a test phase and no stated `tests`-concern result
is not ready for approval. Repeat for verification failures with the new
error fragments (a failing test also re-runs the `tests` concern); state
"no experience match" per concern when none applies. Attach each confirmed
lesson's Lesson and Applies When/Not When sections to the worker prompts
whose concern it matches — a test phase carries the `tests` lessons and its
Conventions line.

## Workflow

`workflow: trivial` is the recorded single-file, obvious, reversible escape
hatch. Full tasks use the following stages.

1. **Intake.** Fetch a named Jira ticket through available tools and read it
   at full fidelity. Use `requirements` to write ticket.md and main.yaml
   together, including full/pinpointed research classification. Resolve
   material open questions before dispatch; reuse answers already supplied.
2. **Branch and research.** Run git recon before research. Preserve existing
   user changes. If the current branch already matches the task, reuse it.
   Otherwise create an isolated worktree or task branch from the fetched
   default branch without moving unrelated changes. Use repository naming
   conventions or `feature/<id>` / `bugfix/<id>` if none exist. Use an
   installed branching skill only if available and applicable. Stop only
   when a conflict cannot be safely resolved within existing authorization.
   Dispatch researcher with Problem and Target; when tests are in scope, the
   topic also names the existing tests of the target members and their test
   project, so the test phase gets anchors. For `research: pinpointed`,
   add `mode: confirm` and verbatim diagnostic rows for every AC. Save its
   brief to research.md. Gaps or misclassification warrant a focused second
   pass before planning. Follow-ups attach the parent map and scope the delta.
3. **Design.** Route experiences, then use `planning` to write work-plan.md
   and verification-plan.md. research.md must already exist. Present both
   plans and obtain any still-needed approval before implementation. Record
   the approval date in main.yaml; retain the files as the durable plan.
   Later scope or strategy changes must be visible as plan diffs.
4. **Implement.** Confirm the task branch. Dispatch one phase at a time to
   its named executor, engineer by default. Include ticket, current phase,
   exact scope, done-when, prior handoff, the lessons matched to the phase's
   concern, and contracts:
   no scope creep, no builds/tests, Roslyn diagnostics for each changed .cs
   file, and explicit deviations. Commit only task files at each coherent
   boundary with `<id>: phase N — <name>`. If commits are disallowed, report
   the missing checkpoint and keep `head` at its last actual commit.
5. **Verify.** Dispatch a fresh reviewer with diff range, gate checks, and
   engineer Deviations/Diagnostics/Handoff sections, never implementation
   transcripts. Reviewer runs gates using `run-build` and `run-test` and
   returns evidence-backed verdicts. On FAIL/PARTIAL, route experiences and
   reason from the failure table and diff. Dispatch researcher if locating
   the cause requires source exploration. Add a fix-phase (`<N>a`, `<N>b`)
   with cause hypothesis, file scope, done-when, and failed checks to rerun.
   Present the plan diff. Continue if existing authorization covers the fix;
   obtain approval for a changed strategy or scope when not already covered.
   Dispatch engineer, then re-gate the failed checks. Three failures of the
   same step without meaningful progress: report evidence and the decision
   needed instead of retrying unchanged work.
6. **Report.** Use `reporting` for inline turn reports and main.yaml updates
   at phase boundaries and gates. Advance `verified` only with a reviewer
   verdict from the current execution, never from an assumption or old run.
7. **Close.** On final-gate PASS, write final-report.md using actual git
   changes and evidence. Prepare the PR body and intended Jira transition.
   Open the PR or update Jira only when the user's instructions authorize
   that external action; otherwise leave the concrete drafts ready for
   approval. Never merge, close, or force-push without explicit instruction.
   Mark main.yaml done for completed implementation/verification and report
   pending publication separately. Use `experiences` if a lesson merits it.

## Delegation and Verification Boundaries

- At most three concurrent workers, subject to the runtime limit. Parallel
  work requires disjoint scopes and no dependency on another worker's writes.
- Dispatches are self-contained; gather missing inputs in the main thread.
  Keep engineer and reviewer contexts separate. Review artifacts, not reasoning.
- Keep remote Jira/GitHub/Confluence operations in the main thread. Workers
  use only the local capabilities their roles permit: Roslyn operations and,
  for reviewer, amtcz build/test tools. These are behavioral restrictions;
  TOML instructions do not create an enforced tool allowlist.
- During full tasks, source mapping belongs to researcher and implementation
  to engineer. The main thread reads task documents and worker outputs.
- Builds/tests belong to reviewer gates, except explicit user requests to
  run them in the main thread. Use the capped companion skills in either case.
- A changed .cs file missing from the engineer's Diagnostics section makes
  the handoff incomplete. Request the missing diagnostics before committing.
- Report deviations before dependent work. Never fabricate gate completion,
  a checkpoint SHA, external publication, or unavailable-tool output.

## Task Folder

```text
docs/tasks/<id>/
  main.yaml              # identity and pipeline state
  ticket.md              # Problem / Target / AC
  research.md
  work-plan.md
  verification-plan.md
  final-report.md         # final gate evidence and draft PR body
```

IDs are lowercased ticket keys, `adhoc-<slug>`, or follow-up
`<parent-id>-fix-<slug>`. Documents have no state frontmatter; main.yaml and
git hold durable state. Turn reports stay inline.
