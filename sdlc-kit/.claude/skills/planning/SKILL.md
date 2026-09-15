---
name: planning
description: Work-plan and verification-plan standards for the SDLC pipeline. Use in plan mode after research.md exists and before any engineer dispatch — when drafting, revising, or splitting phases, or defining verification gates. Governs docs/tasks/<id>/work-plan.md and verification-plan.md, always written as a pair.
---

# Planning Standards

Plans are dispatch material: each phase becomes a self-contained engineer prompt,
and each gate becomes a self-contained reviewer prompt. Write for those consumers.
The plans ship as a pair — a work plan without a verification plan is unreviewable,
and a verification plan without a work plan has nothing to gate.

Plans carry no frontmatter — documents are content, task state lives in
`docs/tasks/<id>/main.yaml` (the `approved` field records plan approval).

## Work Plan — `docs/tasks/<id>/work-plan.md`

```markdown
## Strategy
<2–4 sentences: the chosen approach, and the rejected alternative with one
sentence on why — engineers who don't know why an option lost drift back into it.>

Experience: implementation — <slugs, or none>; tests — <slugs, none, or n/a
(no phase adds or changes tests)>

## Phase 1 — <name>
Goal: <one sentence — what is true at phase end>
Executor: engineer | <specialist agent from installed setup>
Scope: <exact file list — this becomes the executor's fence>
Conventions: <test phases only — framework, naming pattern, and the
fixture/builder helpers to reuse, each anchored to an existing test file>

| Step | Action | File | Anchor | Done-when |
|---|---|---|---|---|
| 1.1 | <one concrete change> | | <member, ~line from research> | <checkable WITHOUT building> |

Exit state: <coherent, committable state — enables checkpoint resume + rollback>

## Explicitly Not Doing
<mirrors ticket out-of-scope plus tempting adjacent improvements>
```

Rules:
- **Research is a precondition, not a field.** `docs/tasks/<id>/research.md`
  must exist on disk before drafting — the orchestrator enforces this; the
  plan does not carry a `based-on` pointer.
- **Phase = dispatch unit.** Size each phase so its prompt (ticket + phase +
  scope) is self-contained; the engineer cannot ask follow-ups.
- **Experience is cited per concern.** The Strategy's Experience line names
  the confirmed slugs for `implementation` and for `tests` separately, from
  the CLAUDE.md experience routing run once per concern. "none" declares that
  the search ran and found nothing; "n/a" that no phase touches tests. A
  plan with a test phase and an empty or missing `tests` entry is not ready
  for approval — the engineer will otherwise write tests from the
  implementation lessons alone.
- **Test phases carry their conventions.** A phase whose Scope adds or
  changes test files fills its `Conventions:` line — framework, naming
  pattern, and the fixture/builder helpers to reuse — each anchored to an
  existing test file from research and to the `tests` slugs in Strategy.
  "Add tests for X" alone makes the engineer invent a style, and the
  resulting inconsistency is a review finding no gate catches. Non-test
  phases omit the line.
- **Name the executor per phase.** Default `engineer`; choose a specialist
  agent from the installed setup when the phase's work matches its speciality
  (e.g. dotnet test generation → the test-generator agent). One executor per
  phase — if a phase seems to need two, it is two phases. The pipeline
  contracts (scope fence, no builds, deviation reporting) travel in the
  dispatch prompt regardless of executor.
- **Prefer fewer, fatter phases.** Every phase is a fresh subagent bootstrap —
  new context, new cache writes, its own rate-limit footprint. Split phases
  for rollback boundaries and scope fences, never for tidiness; if two phases
  would share most of their file scope, they are one phase.
- **Done-when never needs a compiler.** "Method exists with signature X",
  "registration added in Program.cs" — yes. "Tests pass" — no; that's a gate.
- **Every phase boundary is a commit** with message `<id>: phase N — <name>`.
  Order phases so each commit leaves the tree coherent even if work stops there.
- **Independent phases** may be flagged `parallel-ok` for batched dispatch —
  only when their file scopes are disjoint AND neither reads state the other
  writes. When in doubt, sequential.

## Verification Plan — `docs/tasks/<id>/verification-plan.md`

Builds are expensive here. Verification is therefore batched into few gates, not
sprinkled per step — this is the entire reason the two plans are separate files.

```markdown
## Gate Schedule
| Gate | After | Build | Tests | Est. cost |
|---|---|---|---|---|
| G1 | phase <k> | incremental | affected only | ~N min |
| G2 (final) | last phase | full | full suite + all ACs | ~N min |

## Zero-Cost Checks (any time, no build)
<lint on changed files; diff matches scope; no secrets in diff; new or
changed tests match their phase's Conventions line>

## Gate G<n>
| Check | Command | Pass condition | On fail |
|---|---|---|---|

## Regression Watchlist
<from research's boundary/risk rows: behaviors that must not change, checked at final gate>
```

Rules:
- **Default two gates** (mid-point + final). Add a third only when an early
  phase's failure would poison everything after it.
- **Every AC appears as a final-gate row.** Audit by diffing the ticket's AC
  list against G-final before requesting approval — a missing AC means the
  ticket can "pass" unfinished.
- **Every gate row has an On-fail action** (fix-forward scope, or rollback to
  phase-commit SHA). A gate that fails without a defined response stalls the
  pipeline.
- **Gate commands are the capped skills.** Build rows invoke `run-build`,
  test rows invoke `run-test` (`no_build=true` right after a successful
  build) — never raw `dotnet` commands; the reviewer runs the row as written.

## Approval

Present both plans to the human in plan mode and get explicit approval before the
first engineer dispatch. Record the approval date in main.yaml's `approved`
field. Any later change to an approved plan is re-presented as a diff, not
silently rewritten.
