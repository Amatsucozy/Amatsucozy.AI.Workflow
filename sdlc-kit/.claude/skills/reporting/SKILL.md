---
name: reporting
description: Inline turn reports, main.yaml progress fields, and the final report for an active SDLC task. Use at the end of every turn that changed the repo, at phase boundaries and gates, and at task close — docs/tasks/<id>/final-report.md becomes the PR body.
---

# Reporting

Turn reports are inline chat tables, not files. Durable state lives in git
(what changed) and main.yaml (where the pipeline stands). Only the final
report goes to disk, because it outlives the conversation as the PR body.

## Turn Report (end of any turn that changed the repo)

| Phase | Status | Verified | Dispatched | Changed this turn | Deviations |
|---|---|---|---|---|---|
| 2/4 | in-progress | none | engineer ×1 | 3 files (src/Api ×2, tests ×1) | none |

- **Changed this turn** comes from `git diff --stat` plus untracked files from
  `git status --short`, summarized to counts and areas.
- Deviations other than "none" get one line below the table naming the
  file/step and justification. A blocked or needs-decision status gets a line
  with the exact question.
- End with a one-line **Next** when the task continues. On a quiet turn,
  that's all.

## main.yaml Progress

At every phase boundary and gate, update the pipeline-state fields in place —
this is what resume reads:

```yaml
status: in-progress | blocked | verifying | done
phase: "2 of 4"
verified: none | zero-cost | G1 | G2
head: <sha of last phase-boundary commit>
```

Identity fields and `approved` are written earlier and left alone.

## Final Report — `docs/tasks/<id>/final-report.md`

Written once at final-gate PASS; becomes the PR body verbatim. Write it for a
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
<surviving deviations with justification, known limitations, follow-ups>
```

Changes come from git, not memory. Per-turn telemetry isn't persisted, so
close-time stats are reconstructed from phase commits, quoted gate verdicts,
and main.yaml's git history (see the kit's TUNING.md if harder numbers are
needed).
