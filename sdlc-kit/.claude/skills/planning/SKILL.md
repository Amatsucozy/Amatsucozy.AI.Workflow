---
name: planning
description: Work-plan and verification-plan standards for the SDLC pipeline. Use in plan mode after research.md exists and before any engineer dispatch — when drafting, revising, or splitting phases, or defining verification gates. Governs docs/tasks/<id>/work-plan.md and verification-plan.md, always written as a pair.
---

# Planning Standards

Plans are dispatch material: each phase becomes a self-contained engineer
prompt and each gate a self-contained reviewer prompt. They ship as a pair —
a work plan without gates is unreviewable, and gates without a work plan have
nothing to check.

## Work Plan — `docs/tasks/<id>/work-plan.md`

```markdown
## Strategy
<2–4 sentences: the chosen approach, and the rejected alternative with one
sentence on why — engineers who don't know why an option lost drift back into it.>

Experience: implementation — <slugs, or none>; tests — <slugs, none, or n/a>

## Phase 1 — <name>
Goal: <one sentence — what is true at phase end>
Executor: engineer | <specialist agent from the installed setup>
Scope: <exact file list — the executor's fence>
Conventions: <test phases only — framework, naming pattern, fixture/builder
helpers to reuse, each anchored to an existing test file>

| Step | Action | File | Anchor | Done-when |
|---|---|---|---|---|
| 1.1 | <one concrete change> | | <member, ~line from research> | <checkable without building> |

Exit state: <coherent, committable state>

## Explicitly Not Doing
<ticket out-of-scope plus tempting adjacent improvements>
```

- **Experience per concern.** The Experience line comes from routing each
  concern: "none" means the search ran and found nothing, "n/a" means no
  phase touches tests. A plan with a test phase and no `tests` entry isn't
  ready for approval.
- **Test phases fill Conventions**, anchored to existing test files from
  research and to the `tests` slugs. Without it the engineer invents a style
  no gate will catch. Other phases omit the line.
- **One executor per phase**, default `engineer`; pick a specialist agent when
  the work matches its speciality. A specialist whose file lacks the
  engineer's contracts (scope fence, no builds, deviation reporting) gets them
  in its dispatch.
- **Fewer, fatter phases.** Each phase is a fresh subagent bootstrap. Split
  for rollback boundaries and scope fences, not tidiness; phases sharing most
  of their scope are one phase. Size each so its dispatch is self-contained.
- **Done-when never needs a compiler.** "Method exists with signature X" —
  yes. "Tests pass" — that's a gate.
- **Every phase boundary is a commit** (`<id>: phase N — <name>`) that leaves
  the tree coherent.
- **`parallel-ok`** only when file scopes are disjoint and neither phase reads
  state the other writes. When in doubt, sequential.

## Verification Plan — `docs/tasks/<id>/verification-plan.md`

Builds are expensive here, so verification is batched into a few gates.

```markdown
## Gate Schedule
| Gate | After | Build | Tests | Est. cost |
|---|---|---|---|---|
| G1 | phase <k> | incremental | affected only | ~N min |
| G2 (final) | last phase | full | full suite + all ACs | ~N min |

## Zero-Cost Checks (any time, no build)
<lint on changed files; diff matches scope; no secrets; tests match their phase's Conventions>

## Gate G<n>
| Check | Command | Pass condition | On fail |
|---|---|---|---|

## Regression Watchlist
<behaviors from research's boundary/risk rows that must not change; checked at the final gate>
```

- **Two gates by default** (mid-point + final). Add a third only when an early
  phase's failure would poison everything after it.
- **Every AC is a final-gate row.** Diff the ticket's AC list against G-final
  before asking for approval.
- **Every row has an On-fail action** (fix-forward scope or rollback to a
  phase-commit SHA).
- **Gate commands are the skills**: build rows invoke `run-build`, test rows
  `run-test` (`no_build=true` right after a successful build) — never raw
  `dotnet` commands.

## Approval

Present both plans in plan mode and get explicit approval before the first
dispatch; record the date in main.yaml's `approved`. Later changes to an
approved plan are re-presented as a diff.
