# Gate Failure Triage — orchestrator protocol for FAIL/PARTIAL verdicts

Runs whenever a reviewer verdict is FAIL or PARTIAL. Diagnosis is orchestrator
judgment: the reviewer reports facts only (by contract), and the engineer must
never receive raw symptoms without a cause hypothesis — symptom-routed fixes
are where inconsistent, wrong fixes come from.

## The triage block (inline in chat, every FAIL/PARTIAL, before ANY dispatch)

```
## Gate Failure Triage — G<n>, strike <k>
| # | Failure (report row ref) | Root-cause hypothesis | Evidence | Cause location | Confidence |
|---|---|---|---|---|---|

## Proposed Fix
| Failure # | Action | Files | Inside scope fence? | New done-when |
|---|---|---|---|---|

## Plan Impact
none | fix-phase <N>a appended | re-scope (files, why) | re-plan (plan-error cause)
```

Rules for the tables:
- **Every hypothesis cites evidence** — a grep hit, file:line you read, or a
  correlation between report rows ("CS0246 cluster all reference the interface
  renamed in step 2.3"). A hypothesis without evidence is `confidence: low`,
  and low confidence forces the approval tier below. Vibes route to humans,
  never to engineers.
- **Group cascades.** One root-cause row may cover many failure rows — list
  the covered row numbers. Diagnose the FIRST error; downstream missing-type
  noise is usually its shadow.
- **Cause location** is one of: `in-phase` (introduced by the phase under
  review), `pre-existing` (was broken before), `upstream-drift` (someone
  else's change on the base branch), `plan-error` (the plan itself directed
  the wrong change). Anything other than `in-phase` means the plan — not the
  engineer — was wrong, and is never auto-dispatched.

## Dispatch tiers

**Auto-dispatch** (triage block still shown, no wait) requires ALL of:
strike 1 · every fix inside the original scope fence · every row
`confidence: high` · every cause `in-phase` · Plan Impact is `none` or
`fix-phase appended`.

**Human approval required** if ANY of: a fix crosses the scope fence · any
cause location other than `in-phase` · any confidence below high · the
reviewer reported `scope-drift` or `gate-gap` · strike ≥ 2 · Plan Impact is
re-scope or re-plan. Present the triage block and wait; the approved fix is a
plan change and follows the plan-diff rule.

Strike 3 remains the hard stop: summarize attempts to the human and wait —
no fourth dispatch under any tier.

## Before dispatching (both tiers)

1. **Write the fix into the plan first.** Append it to `work-plan.md` as
   fix-phase `<N>a` (`<N>b`, ...) per the planning skill's fix-phase format.
   The reviewer verifies against the plan; a fix that exists only in chat
   becomes a false scope-drift finding or an unverified change at re-gate.
2. Update ticket frontmatter `strikes`.
3. The fix dispatch carries: the relevant triage row(s) verbatim, the
   hypothesis, the constraint **"fix the cause named in row <#>; if evidence
   shows the hypothesis is wrong, report `blocked` — do not fix the
   symptom"**, the fix-phase's done-when, and the standard pipeline contracts.
4. **Re-gate narrowly:** rerun only the failed gate's failing checks
   (incremental build; `--filter` to affected tests) — the full schedule
   reruns only if the fix crossed scope.

## Repeat-failure escalation

The same root-cause class appearing twice — within a task or across tasks —
is an experiences-entry candidate (write bar: generalizable cause). The fix
loop is where lessons surface; the experience layer is where they stop the
class from being introduced at planning time.
