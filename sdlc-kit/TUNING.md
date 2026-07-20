# Tuning Register

Every threshold below is a starting guess, not a law. Each lists where it
lives, why it was chosen, and the signal that should trigger revisiting it.
When you change one based on run evidence, note the change here and consider
an experiences entry (domain: process).

| Constant | Value | Lives in | Rationale | Revisit when |
|---|---|---|---|---|
| Researcher search budget | 3 Glob + 8 Grep | agents/researcher.md | Haiku loops without hard caps | "Not Searched" sections are routinely non-empty on ordinary tasks (raise), or budgets never approached (lower) |
| Researcher read window | ±30 lines / full file <150 | agents/researcher.md | token cost control | briefs keep missing context adjacent to hits |
| Concurrent subagents | max 3 | skills/sdlc-orchestrator | Bedrock RPM spikes from fan-out | provider quota changes, or throttling observed at 3 |
| Engineer retry limit | 3 strikes | agents/engineer.md, skills/sdlc-orchestrator | classic escalation heuristic | strikes exhausted on trivially fixable issues (raise), or long doomed retry chains (lower) |
| Gate count default | 2 (mid + final) | skills/planning | build cost dominates | PARTIAL/FAIL verdicts cluster at G-final with root causes in early phases → add earlier gate |
| PR review size cap | ~1500 changed lines | agents/pr-reviewer.md | responsible-review ceiling | honest-partials are frequent on normal team PRs |
| Nit cap per review | "a handful" | agents/pr-reviewer.md | anti-noise | colleagues report reviews feel nitpicky or toothless |
| Orchestrator skill length | ~150 lines | skills/sdlc-orchestrator | instruction-following degrades past this | rules demonstrably ignored → cut or promote to output style. NOTE: dispatch-enforcement patch grew the skill — run `wc -l` and either raise this number here or promote before the next ticket; an unexamined breach makes the row a fiction |
| Dispatch routing enforcement | hard prohibitions + artifact gates (all three roles) | agents/researcher.md, agents/reviewer.md, agents/engineer.md, skills/sdlc-orchestrator | week-one evidence: procedure-phrased steps alone did not route researcher/reviewer work to subagents; enforcement shape upgraded per the erosion rule | gates never fire across 10+ tickets AND transcripts show routing held without them → soften back to procedure language (mechanical enforcement must keep earning its place, both directions) |
| Fresh-session rehydration | mandatory batched read at resume: main.yaml, ticket, work-plan (Strategy + phase under review + fix-phases), gate, research | skills/sdlc-orchestrator On Invocation §1 | a fresh session holds none of the plan's context; approved Strategy stays binding across sessions | rehydrated documents routinely go unused in the resumed session's decisions → trim the read set; or resumed fixes still depart from Strategy → the read isn't the problem, the binding language is |
| `ready` status value | DEFERRED — not added to main.yaml status enum | (would live in skills/requirements, skills/sdlc-orchestrator step 1) | intake/execution session split under evaluation; adding a status before the leak is observed is speculative guardrail | a draft ticket (open questions, non-binary AC) reaches research or plan mode in a dev session → add `ready` + audit-or-bounce guard in orchestrator step 1 |
| Turn-report trigger | any turn that changed the repo | sdlc-orchestrator step 6 (inline table; loop files retired for token cost) | "no silent work" | resume quality degrades or tuning needs hard telemetry → resume file-based reports |
| main.yaml update discipline | instruction-only (reporting skill; no hook) | skills/reporting, sdlc-orchestrator step 6 | hooks retired on no-observed-value; ~5–8 writes per task don't justify a per-turn reminder riding every cache read. <!-- CONFIRM: if no stale-at-resume across the first 5 tickets, promote this rationale to observed-holding and note the date --> | main.yaml stale at any resume in the first 5 tickets → add a conditional Stop hook (warn only when last `<id>: phase N` commit disagrees with main.yaml phase), not a blind reminder |
| Experience write bar | >30 min generalizable failure | skills/experiences | noise control | layer grows fast with entries never retrieved (raise), or repeated re-learning (lower) |

Reading the evidence: per-turn telemetry files were retired with loop reports —
close-time stats are best-effort by design (reporting skill). The evidence
sources for this register are: phase-boundary commits (`git log --grep
'^<id>: phase'`), reviewer verdicts quoted in-session (the `verified` field
advances only on those), and main.yaml's own git log (the state timeline —
staleness at resume shows up as a gap between its last diff and the last
phase commit). Five tasks of that record is enough to move most of these
numbers. If a decision needs harder numbers than these reconstruct, the
escalation is resuming file-based telemetry — that reversal signal lives in
the turn-report row above.

## Token & RPM constants (added after efficiency review)

| Constant | Value | Lives in | Rationale | Revisit when |
|---|---|---|---|---|
| Researcher turn shape | 3–4 batched turns | agents/researcher.md | each turn = 1 request; sequential calls re-read full context | briefs degrade because batched queries can't build on each other's results |
| Bash output caps | tail -20 (engineer) / tail -40 (reviewer) | agent files | log dumps ride in every later cache read | truncation hides root causes at gates |
| Uneventful-turn report | table row only | skills/reporting | ~40 tokens per quiet turn | table-only turns hide information the human needed |
| Git-derived changed files | head -40 at resume | sdlc-orchestrator On Invocation | replaces hand-maintained cumulative tables | tasks routinely touch >40 files |
| Phase count bias | fewer, fatter | skills/planning | each dispatch = context bootstrap + RPM footprint | fat phases raise engineer-blocked telemetry |

## Awaiting run evidence — open questions

Rows above that only ticket logs can move. Answer from the record, not memory;
strike each line once resolved (update the row, note the date).

- **Researcher budgets:** were "Not Searched" sections non-empty on ordinary
  (non-sprawling) tasks? Check saved `research.md` files.
- **Concurrent cap:** any Bedrock throttling observed at 3? Any turn where a
  4th parallel dispatch was wanted?
- **Gate count:** did any FAIL/PARTIAL at G-final trace to a phase before the
  mid-gate? Check fix-phase entries in work-plans.
- **Phase sizing:** any `blocked` engineer reports attributable to fat phases
  (scope fence too wide to hold in one dispatch)?
- **main.yaml staleness:** any resume where main.yaml's phase disagreed with
  the last phase commit? (Resolves the CONFIRM marker in the discipline row.)
- **Orchestrator line count:** current `wc -l` vs ~150. (Resolves the NOTE in
  the length row.)