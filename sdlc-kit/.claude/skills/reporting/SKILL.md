---
name: reporting
description: Inline turn reports, main.yaml progress fields, and the final report for an active SDLC task. Use at the end of every turn that changed the repo, at phase boundaries and gates, and at task close — docs/tasks/<id>/final-report.md becomes the PR body.
---

# Reporting

Reports are inline chat tables, not files — the human reads them in the flow of
the conversation, and durable state lives in exactly two places: git (what
changed) and main.yaml (where the pipeline stands). Only the final report is
written to disk, because it outlives the conversation as the PR body.

## Turn Report (inline, end of any turn that changed the repo)

One table plus at most two lines. Uneventful turns get the table only.

| Phase | Status | Verified | Dispatched | Changed this turn | Deviations |
|---|---|---|---|---|---|
| 2/4 | in-progress | none | engineer ×1 | 3 files (src/Api ×2, tests ×1) | none |

- **Changed this turn** comes from git (`git diff --stat`, plus untracked
  task files from `git status --short`, which diff omits), summarized to
  counts and areas — never a hand-written file list.
- **Deviations** ≠ "none" requires one line below the table naming the
  file/step and the justification. Blocked/needs-decision status requires a
  line with the exact question for the human.
- End with a one-line **Next** when the task continues.

## Durable Progress — `docs/tasks/<id>/main.yaml`

At every phase boundary and gate, update the pipeline-state fields of
main.yaml — this is what resume reads:

```yaml
status: in-progress | blocked | verifying | done
phase: "2 of 4"
verified: none | zero-cost | G1 | G2
head: <sha of last phase-boundary commit>
```

Four mutable fields, updated in place (the identity fields and `approved`
above them are written earlier and left alone) — a few tokens per boundary,
and combined with git it reconstructs full task state at any resume. Since
every transition is a diff to this one file, its git log doubles as the task's
state timeline.

## Final Report — `docs/tasks/<id>/final-report.md` (at close)

Written once, at final-gate PASS; becomes the PR body verbatim. Write it for a
colleague who saw none of the conversation.

```markdown
# <id> — <title>

## What & Why
<3–5 sentences from the ticket's Problem/Target, past tense>

## How
<the Strategy that won, including what was rejected and why — one paragraph>

## Changes
<from `git diff --name-status <base>...HEAD`, annotated with one-clause whys>

## Verification
<gates run, verdicts, AC-by-AC outcome with evidence pointers>

## Notes for Reviewers
<deviations that survived (with justification), known limitations, follow-ups>
```

Known limitation: per-turn telemetry is not persisted, so pipeline stats at
close are best-effort — phase-boundary commits, quoted gate verdicts, and
main.yaml's git history reconstruct most of it. If tuning decisions need
harder numbers, the escalation is file-based telemetry (see the kit's
TUNING.md).
