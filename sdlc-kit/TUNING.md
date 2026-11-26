# Tuning Register

Every threshold below is a starting guess, not a law. Each lists where it
lives, why it was chosen, and the signal that should trigger revisiting it.
When you change one based on run evidence, note the change here and consider
an experiences entry (domain: process).

| Constant | Value | Lives in | Rationale | Revisit when |
|---|---|---|---|---|
| Researcher search budget | none — stop at convergence (new searches surface only catalogued files), partial map if long | agents/researcher.md | hard caps were for an older Haiku that looped without them; the brief's Not Searched section records what was skipped | briefs come back sprawling or the researcher loops → reinstate a cap; or Not Searched is routinely non-empty on ordinary tasks → the stop rule is too eager |
| Researcher read window | ±30 lines; whole file only when short or the topic's center | agents/researcher.md | token cost control | briefs keep missing context adjacent to hits |
| Concurrent subagents | max 3 | skills/sdlc-orchestrator | Bedrock RPM spikes from fan-out | provider quota changes, or throttling observed at 3 |
| Engineer retry limit | 3 strikes | agents/engineer.md, skills/sdlc-orchestrator | classic escalation heuristic | strikes exhausted on trivially fixable issues (raise), or long doomed retry chains (lower) |
| Gate count default | 2 (mid + final) | skills/planning | build cost dominates | PARTIAL/FAIL verdicts cluster at G-final with root causes in early phases → add earlier gate |
| PR review size cap | ~1500 changed lines | agents/pr-reviewer.md | responsible-review ceiling | honest-partials are frequent on normal team PRs |
| Nit cap per review | "a handful" | agents/pr-reviewer.md | anti-noise | colleagues report reviews feel nitpicky or toothless |
| Orchestrator skill length | ~150 lines target; 148 actual (2026-11-26) | skills/sdlc-orchestrator | instruction-following degrades past this | rules demonstrably ignored → cut or promote. 2026-11-26 streamlining pass (212 → 148 lines): rules kept, repetition removed — main.yaml/state, pinpointed-still-researches, and builds-at-gates rules now live once in their owning skill (requirements, planning, reviewer) and are referenced by name |
| Dispatch routing enforcement | hard prohibitions + artifact gates (all three roles); dispatch-precedence stated once per agent + the orchestrator's Dispatch Contract | agents/researcher.md, agents/reviewer.md, agents/engineer.md, skills/sdlc-orchestrator | week-one evidence: procedure-phrased steps alone did not route researcher/reviewer work to subagents; enforcement shape upgraded per the erosion rule. 2026-11-26: the prohibitions and gates stay; the repeated 6-line precedence block and the mandatory closing sentence on every dispatch were removed as redundant layers | dispatches start prescribing method again, or agents follow dispatch method over their own file → restore the closing sentence first (cheapest layer); gates never fire across 10+ tickets AND routing held → soften back to procedure language |
| Fresh-session rehydration | mandatory batched read at resume: main.yaml, ticket, work-plan (Strategy + phase under review + fix-phases), gate, research | skills/sdlc-orchestrator On Invocation §1 | a fresh session holds none of the plan's context; approved Strategy stays binding across sessions | rehydrated documents routinely go unused in the resumed session's decisions → trim the read set; or resumed fixes still depart from Strategy → the read isn't the problem, the binding language is |
| `ready` status value | DEFERRED — not added to main.yaml status enum | (would live in skills/requirements, skills/sdlc-orchestrator step 1) | intake/execution session split under evaluation; adding a status before the leak is observed is speculative guardrail | a draft ticket (open questions, non-binary AC) reaches research or plan mode in a dev session → add `ready` + audit-or-bounce guard in orchestrator step 1 |
| Turn-report trigger | any turn that changed the repo | sdlc-orchestrator step 6 (inline table; loop files retired for token cost) | "no silent work" | resume quality degrades or tuning needs hard telemetry → resume file-based reports |
| main.yaml update discipline | instruction-only (reporting skill; no hook) | skills/reporting, sdlc-orchestrator step 6 | hooks retired on no-observed-value; ~5–8 writes per task don't justify a per-turn reminder riding every cache read. <!-- CONFIRM: if no stale-at-resume across the first 5 tickets, promote this rationale to observed-holding and note the date --> | main.yaml stale at any resume in the first 5 tickets → add a conditional Stop hook (warn only when last `<id>: phase N` commit disagrees with main.yaml phase), not a blind reminder |
| Experience write bar | >30 min generalizable failure | skills/experiences | noise control | layer grows fast with entries never retrieved (raise), or repeated re-learning (lower) |
| Experience routing concerns | `implementation` always + `tests` when the work adds/changes/fixes tests; one `exp_search` per concern; per-concern declaration in Strategy; test phases carry a `Conventions:` line | CLAUDE.md routing steps 1/3/4/5, skills/sdlc-orchestrator steps 2/3/5 + Dispatch Contract, skills/planning | observed 2026-09-14: routing ran once on the implementation problem statement, so test lessons were never searched even when the task wrote or fixed tests, and engineers invented test style — inconsistent tests that no gate catches | `tests`-concern searches return zero confirmed matches across 10+ test-writing tasks (the corpus has no test lessons — fix the write bar, not the routing); or test phases still drift with the lessons and Conventions attached (attachment isn't the failure — look at the engineer prompt) |
| MCP tool guidance placement | in each MCP server: per-tool docstrings + server `instructions` (cross-tool workflow, verdict handling); CLAUDE.md keeps a one-line-per-server map and kit policy (gates, no raw logs) | amtcz-mcp, dbschema-mcp, roslyn-mcp server.py; CLAUDE.md → MCP Servers | 2026-11-26: the ~1,500-word inlined scenario tables rode in every session and were triplicated across Claude/Codex/Devin files. Server instructions keep the always-visible property that motivated inlining (they are not skill-triggered: Claude Code and Codex show them whenever the server is connected) while loading only with the server. Earlier history: the `amtcz-cli` skill was retired because a skill description is a fragile trigger | wrong-call incidents rise after the move → check the harness actually surfaces server `instructions` and inline only the missing server's verdict table there (Devin is unconfirmed, so `.devin/agents` already spell out roslyn verdict handling instead of deferring to the server); tests assert each server publishes instructions with a ≤512-char lead paragraph (Codex reads that first) |

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
| Researcher turn shape | batch independent calls each turn | agents/researcher.md | each turn = 1 request; sequential calls re-read full context. The prescribed Glob→Grep→roslyn→Read order per turn was dropped 2026-11-26 as over-specified | briefs degrade because batched queries can't build on each other's results |
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
- ~~**Orchestrator line count:** current `wc -l` vs ~150.~~ Examined
  2026-09-12: 184 lines after the optimization pass; the length row now
  carries the actual count and the promotion-not-trim reversal signal.
- **amtcz manual inlining:** did wrong-command/wrong-flag incidents actually
  drop after CLAUDE.md absorbed the full manual, relative to the skill-based
  baseline? Check engineer/reviewer dispatch transcripts and researcher
  "Not Searched"-style admissions for `amtcz` misuse, pre- vs post-change.