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
| Orchestrator skill length | ~150 lines | skills/sdlc-orchestrator | instruction-following degrades past this | rules demonstrably ignored → cut or promote to output style |
| Turn-report trigger | any turn that changed the repo | sdlc-orchestrator step 6 (inline table; loop files retired for token cost) | "no silent work" | resume quality degrades or tuning needs hard telemetry → resume file-based reports |
| Experience write bar | >30 min generalizable failure | skills/experiences | noise control | layer grows fast with entries never retrieved (raise), or repeated re-learning (lower) |

Reading the evidence: loop-report telemetry (reporting skill) sums into each
task's final-report Pipeline Stats. Five tasks of stats is enough to justify
moving most of these numbers.

## Token & RPM constants (added after efficiency review)

| Constant | Value | Lives in | Rationale | Revisit when |
|---|---|---|---|---|
| Researcher turn shape | 3–4 batched turns | agents/researcher.md | each turn = 1 request; sequential calls re-read full context | briefs degrade because batched queries can't build on each other's results |
| Bash output caps | tail -20 (engineer) / tail -40 (reviewer) | agent files | log dumps ride in every later cache read | truncation hides root causes at gates |
| Uneventful-turn report | table row only | skills/reporting | ~40 tokens per quiet turn | table-only turns hide information the human needed |
| Git-derived changed files | head -40 at resume | sdlc-orchestrator On Invocation | replaces hand-maintained cumulative tables | tasks routinely touch >40 files |
| Phase count bias | fewer, fatter | skills/planning | each dispatch = context bootstrap + RPM footprint | fat phases raise engineer-blocked telemetry |
