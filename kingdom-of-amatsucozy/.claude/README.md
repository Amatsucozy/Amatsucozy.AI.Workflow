# Amatsucozy v3

Structured software design and implementation workflow. Three commands, four agents, model-tiered sub-agents, context-disciplined brief files, templates bundled inside their owning skills.

---

## Cast

| Agent | Model | Role |
|---|---|---|
| **King** | Sonnet | Main agent · Amatsucozy persona · writes docs · holds state |
| **Scout** | Haiku | Codebase investigation · writes brief files · dies after each run |
| **Steward** | Haiku | Implementation planning · writes plan file · dies after each run |
| **Knight** | Sonnet | Code execution · test-first · failure escalation · dies after each run |
| **Chancellor** | Haiku | Post-execution audit · validates execution vs design + plan · manual only |
| **Sentinel** | — (skill) | Phase gate authority · consulted at every phase boundary |

---

## Commands

| Command | Shorthand | Flow |
|---|---|---|
| `*activate` | — | Greet + Status Block + wait |
| `*start-workflow [--auto]` | `*sw` | Scout → King writes design → Steward → Knight |
| `*create-architecture-doc` | `*cad` | Scout → King writes 7-file arch set |
| `*implement` | `*i` | Knight executes existing plan |
| `*audit` | — | Chancellor validates execution vs design + plan (manual, post-completion) |

---

## File structure

```
.amtcz/
  briefs/
    {feature_id}-scout.md      ← Scout scope map (≤400 tokens)
    {feature_id}-impact.md     ← Scout conflict check (≤400 tokens)
    {feature_id}-blocker.md    ← Knight failure escalation
  checkpoints/
    {feature_id}.md            ← King phase checkpoint (session resume)
  audits/
    {feature_id}-audit.md      ← Chancellor audit report (written on *audit)

.claude/
  agents/
    king.md                    ← Sonnet · main agent
    scout.md                   ← Haiku · investigation sub-agent
    steward.md                 ← Haiku · planning sub-agent
    knight.md                  ← Sonnet · implementation sub-agent
    chancellor.md              ← Haiku · post-execution audit sub-agent
  skills/
    sentinel/
      SKILL.md                 ← gate logic · cached (cache_control: ephemeral)
    king/
      assets/
        checkpoint-template.md ← checkpoint schema + resume instructions
    design-doc-writer/
      SKILL.md
      assets/
        task-design-template.md
      references/
        ascii-diagram-rules.md
    imp-plan-writer/
      SKILL.md
      assets/
        implementation-plan-template.md
    arch-doc-writer/
      SKILL.md
      assets/
        architecture-doc-template.md
      references/
        file-structure.md
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
    {feature_id}.md            ← Phase 1 output (design doc)
    {feature_id}-plan.md       ← Phase 2 output (implementation plan)
  architecture/
    README.md                  ← index
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

**Templates inside skills.** Each skill owns its template in `assets/`. No `.amtcz/templates/` directory. The skill is the unit of deployment — templates travel with the skill that uses them.

**feature_id.** Kebab-case slug derived by King at `*sw` time. Immutable for the lifecycle of the workflow. Used in every brief, checkpoint, design doc, and plan filename.

**Checkpoint schema.** Defined in `skills/king/assets/checkpoint-template.md`. Six fields: feature_id, phase, auto flag, design_doc path, plan_doc path, last_step. Enables session resume without conversation history replay.

**Model routing.** Scout + Steward on Haiku (retrieval + structured formatting). King + Knight on Sonnet (judgment + code). ~60% token cost reduction on full `*sw --auto` runs.

**Brief files on disk.** Scout writes ≤400-token structured briefs. King reads only the brief — never raw traversal output. Sub-agent context window lives and dies between spawns.

**Sentinel cached.** `cache_control: ephemeral` on Sentinel SKILL.md. Prevents re-ingestion on every phase boundary call.

**Status Block owned by King.** Single definition in `agents/king.md`. Removed from Sentinel to eliminate duplication and drift risk.

---

## Changes from v2

- Templates moved from `.amtcz/templates/` into `skills/{skill}/assets/`
- Checkpoint schema defined in `skills/king/assets/checkpoint-template.md`
- `feature_id` format and ownership explicitly defined in King
- Sub-agent spawn mechanism described in King's **Sub-agent spawn** section
- Status Block removed from Sentinel — owned by King only
- `cache_control: ephemeral` added to Sentinel frontmatter
- Sentinel now uses `feature_id` consistently (was `feature` in v2 — naming inconsistency fixed)
- King workflow steps expanded to include checkpoint writes at each phase boundary
