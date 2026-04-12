# Amatsucozy v2

Structured software design and implementation workflow enforcing a 3-phase lifecycle with gated transitions, model-tiered sub-agents, and context-disciplined brief files.

---

## Cast

| Agent | Model | Role | Spawned by |
|---|---|---|---|
| **King** | Sonnet | Main agent · Amatsucozy persona · writes docs | User |
| **Scout** | Haiku | Codebase investigation · writes brief files | King |
| **Steward** | Haiku | Implementation planning · writes plan file | King |
| **Knight** | Sonnet | Code execution · test-first · failure escalation | King |
| **Sentinel** | — (skill) | Phase gate authority · shared by all agents | King reads |

---

## Commands

| Command | Shorthand | Flow |
|---|---|---|
| `*activate` | — | Greet + Status Block + wait |
| `*start-workflow [--auto]` | `*sw` | Scout → King writes design → Steward → Knight |
| `*create-architecture-doc` | `*cad` | Scout → King writes 7-file arch set |
| `*implement` | `*i` | Knight executes existing plan |

---

## File structure

```
.amtcz/
  core/
    amatsucozy.md              ← King system prompt (≤800 tokens)
  briefs/
    {feature}-scout.md         ← Scout scope map (≤400 tokens, deleted on completion)
    {feature}-impact.md        ← Scout conflict check (≤400 tokens, deleted on completion)
    {feature}-blocker.md       ← Knight failure escalation (kept until resolved)
  checkpoints/
    {feature}.md               ← King phase checkpoint (used for session resume)
  templates/
    task-design-template.md
    implementation-plan-template.md
    architecture-doc-template.md

.claude/
  agents/
    king.md                    ← Sonnet · main agent
    scout.md                   ← Haiku · investigation sub-agent
    steward.md                 ← Haiku · planning sub-agent
    knight.md                  ← Sonnet · implementation sub-agent
  skills/
    sentinel/
      SKILL.md                 ← gate logic · ≤300 tokens · cached
    design-doc-writer/
      SKILL.md
      references/
        ascii-diagram-rules.md
    arch-doc-writer/
      SKILL.md
      references/
        file-structure.md
    imp-plan-writer/
      SKILL.md
    code-implementer/
      SKILL.md
    source-fast-search/        ← existing · unchanged
      SKILL.md
    source-navigator/          ← existing · unchanged
      SKILL.md
    source-indexer/            ← existing · unchanged
      SKILL.md
    source-analyzer/           ← existing · unchanged
      SKILL.md
      parsers/

docs/
  tasks/
    {feature}.md               ← Phase 1 output
    {feature}-plan.md          ← Phase 2 output
  architecture/
    README.md
    {module}/
      README.md
      architecture.md
      api-specification.md
      implementation-guide.md
      integration.md
      operations.md
      deployment.md
```

---

## Key design decisions

**Model routing.** Scout and Steward run on Haiku — lookup and formatting tasks. King and Knight run on Sonnet — judgment and code. ~60% token cost reduction on `*sw --auto` vs uniform Sonnet.

**Brief files on disk.** Scout writes a ≤400-token structured brief. King reads only the brief, never raw traversal output. Sub-agent context window lives and dies without polluting King.

**King context budget.** King stores path + 3-line summary per completed phase doc, never full content. Checkpoints allow session resume without history replay.

**Knight failure recovery.** 3-strike escalation: retry twice with different approaches, then write a blocker file and surface to King. Resume protocol: find first unchecked step and continue.

**Sentinel scope split.** New workflow gate and resume gate are separate sections. Sentinel is read at every phase boundary — kept slim (≤300 tokens) and structured for prompt caching.

**Source skills unchanged.** `source-navigator`, `source-fast-search`, `source-indexer`, `source-analyzer` are production-quality and unchanged. Scout is a thin wrapper that dispatches to the right one per query type.

---

## Token estimates

| Scenario | v1 estimate | v2 estimate | Saving |
|---|---|---|---|
| Simple bug fix `*sw` | ~18k | ~8k | 56% |
| Medium feature `*sw --auto` | ~55k | ~22k | 60% |
| Large refactor `*sw --auto` | ~120k+ | ~45k | 63% |
| `*cad` large module | ~40k | ~18k | 55% |

---

## Removed from v1

- `ticket-id-assigner` skill — removed (ticket IDs removed from workflow)
- `business-doc-writer` skill — removed (focus: architecture + engineering only)
- `design.md` agent — absorbed into King
- `orchestrator.md` agent — absorbed into King
- `planner.md` agent — replaced by Steward
- `implementer.md` agent — replaced by Knight
- `doc-writer.md` agent — absorbed into King (`*cad` flow)
- `gate-enforcer` skill — replaced by Sentinel (slimmer, split, cached)
