# Amatsucozy — Design Consolidation Plan

> **Score before:** 54/100  
> **Target:** 80+/100  
> **Ref:** Critical analysis — context window discipline, token efficiency, brief protocol, failure recovery

---

## Cast (post-simplification)

| Name | Type | Model tier | Replaces |
|---|---|---|---|
| **King** | Main agent · Amatsucozy persona | Sonnet | Orchestrator + Design agent |
| **Scout** | Sub-agent · spawned, dies | Haiku | Design agent (investigation) + Impact analyzer |
| **Steward** | Sub-agent · spawned, dies | Haiku | Planner agent |
| **Knight** | Sub-agent · spawned, dies | Sonnet | Implementer agent |
| **Sentinel** | Shared skill | — | gate-enforcer |

**Removed:** ticket-id-assigner, business-doc-writer, design agent (absorbed into King), impact analyzer (absorbed into Scout)

**Commands (3 only):**
- `*sw [--auto]` — Scout → King writes design → Steward writes plan → Knight implements
- `*cad` — Scout investigates → King writes architecture docs
- `*i` — Knight executes existing plan

---

## Fix 1 — Model Routing

**Problem:** All agents run on the same model. Scout (lookup) and Steward (formatting) cost as much as King (judgment).

**Solution:** Declare model tier per agent. Haiku for retrieval and structured formatting. Sonnet for creative judgment and code.

- [ ] Add `model: haiku` to Scout agent header
- [ ] Add `model: haiku` to Steward agent header
- [ ] Add `model: sonnet` to Knight agent header
- [ ] Add `model: sonnet` to King agent header
- [ ] Document routing rationale in README

**Expected saving:** ~60% token cost reduction on `*sw --auto` runs.

---

## Fix 2 — Brief File Schema

**Problem:** Brief file format is undefined. Without a size cap, Scout can write a 10k-token brief that repollutes King's context when read — defeating the isolation.

**Solution:** Hard schema with a 400-token cap. Two brief types: `scout.md` (what exists) and `impact.md` (what conflicts). Scout writes both.

### Scout brief schema (`/.amtcz/briefs/{id}-scout.md`)

```markdown
# Scout Brief · {id}
Generated: {ISO timestamp}
Query: {one-line description of what was asked}

## Affected files
| File | Layer | Relevant entities |
|---|---|---|
| path/to/file.py | Service | ClassName.method_name |
(max 8 rows)

## Dependency chain
(max 5 hops, one line each)
1. EntryClass → DependencyA → DependencyB

## Conflicts
- NONE | {list any AMTCZ tickets or stale flags found}

## Gaps
- NONE | {list any [STALE] or [UNRESOLVED] entries encountered}
```

### Impact brief schema (`/.amtcz/briefs/{id}-impact.md`)

```markdown
# Impact Brief · {id}
Generated: {ISO timestamp}
Proposed changes: {component list from design doc}

## Conflict check
| Component | Status | Note |
|---|---|---|
| path/to/file.py | SAFE | no other tickets touch this |
| path/to/other.py | CONFLICT | AMTCZ-003 modifies same file |

## Missing index coverage
- NONE | {files proposed for change that are not in context.md}

## Verdict
SAFE TO PROCEED | CONFLICTS FOUND | INDEX INCOMPLETE
```

- [ ] Write `/.amtcz/briefs/` directory convention to README
- [ ] Add brief schemas to Scout agent definition
- [ ] Add brief-read instruction to King agent (reads both briefs, 400-token budget)
- [ ] Add brief staleness rule: regenerate if older than current session or if source files modified
- [ ] Add brief cleanup: Knight deletes briefs on successful completion

---

## Fix 3 — King Context Budget

**Problem:** King accumulates system prompt + conversation history + scout brief + design doc + imp plan + partial code across phases. Hits 100k+ on large features.

**Solution:** Explicit context budget per phase. King prunes at defined checkpoints.

### King context budget

| Phase | King holds | King drops |
|---|---|---|
| Before Scout | system prompt + user query | — |
| After Scout brief | + scout brief (≤400 tokens) | raw query |
| After design doc written | + design doc path reference | scout brief |
| After imp plan written | + imp plan path reference | design doc content |
| During Knight | + checkpoint summary | imp plan content |

**Path reference rule:** King never re-reads the full design doc or imp plan into context. It stores the file path and a 3-line summary. Sub-agents read the full file themselves.

- [ ] Add context budget table to King agent definition
- [ ] Add "path reference only" rule — King stores `docs/tasks/{id}-name.md` + 3-line summary, not full content
- [ ] Add checkpoint protocol: after each phase, King writes a 5-line session checkpoint to `/.amtcz/checkpoints/{id}.md`
- [ ] Add resume protocol: if session interrupted, King reads checkpoint file to restore state without full history replay

---

## Fix 4 — Knight Failure Recovery

**Problem:** If Knight fails mid-execution, partial checkboxes in the plan create ambiguous state. No defined resume or rollback path.

**Solution:** Resume protocol (find first unchecked step) + failure escalation (3 strikes → surface to King).

### Knight resume protocol
1. Read plan file
2. Find first step where `**Verification:** [ ]` exists
3. Execute from that step forward
4. If step has been attempted before (detected by a `<!-- attempted: N -->` comment), increment attempt counter

### Knight failure escalation
- Attempt 1 fails → retry with different approach, note in plan
- Attempt 2 fails → retry once more, note in plan
- Attempt 3 fails → write blocker to `/.amtcz/briefs/{id}-blocker.md`, surface to King, stop

### Blocker file schema (`/.amtcz/briefs/{id}-blocker.md`)
```markdown
# Blocker · {id} · Step {N}
Step: {title}
File: {path}
Attempted: 3 times
Error: {description of what failed}
Options:
- {option A}
- {option B}
```

- [ ] Add resume protocol to Knight agent definition
- [ ] Add failure escalation (3-strike rule) to Knight agent definition
- [ ] Add blocker file schema to Knight agent definition
- [ ] Add blocker handling to King: reads blocker file, presents options to user, re-enters Sentinel gate

---

## Fix 5 — Sentinel Scope Narrowing

**Problem:** Sentinel is read for both `*sw` (new workflow) and `*i` (resume) with the same document, but the gate logic differs. Also re-ingested on every phase boundary without caching.

**Solution:** Split Sentinel into two focused sections (new vs resume). Mark the skill for extended prompt caching.

- [ ] Split Sentinel into `## New workflow gate` and `## Resume gate` sections
- [ ] Add `cache_control: ephemeral` marker comment to Sentinel SKILL.md header (signals Claude API to cache this skill's content at the prompt boundary)
- [ ] Remove Status Block format from Sentinel — move to King's own definition (Sentinel should only do gate logic, not formatting)
- [ ] Trim Sentinel to under 300 tokens total — it is read on every phase boundary, every token counts

---

## Fix 6 — Scout Skill Dispatch

**Problem:** Scout has no defined contract for which skills to invoke per query type. It could run all three source skills when only fast-search was needed.

**Solution:** Decision tree in Scout's agent definition.

### Scout skill dispatch rules
```
Query type                          → Skill to use
─────────────────────────────────────────────────
"what file handles X?"              → source-fast-search only
"trace the path from A to B"        → source-navigator only
"list all classes in module Y"      → source-fast-search only
"what depends on class Z?"          → source-navigator only
"context.md missing or stale"       → source-indexer → then fast-search
"full codebase not indexed"         → source-analyzer → source-indexer
```

- [ ] Add dispatch decision tree to Scout agent definition
- [ ] Add token budget to Scout: fast-search ≤ 5k tokens, navigator ≤ 15k tokens (5 hops max, enforced)
- [ ] Add Scout output contract: brief must be written before Scout exits regardless of traversal result

---

## Fix 7 — System Prompt Size

**Problem:** `amatsucozy.md` system prompt is ~2k tokens re-ingested on every turn. King agent definition compounds this with routing table, status block format, and hard rules.

**Solution:** Slim King's always-on context to the minimum. Move reference content to skills read on demand.

### King always-on context (target: ≤800 tokens)
- Persona statement (3 lines)
- Command routing table (6 rows)
- Status block format (8 lines)
- Hard rules (5 bullets)
- Pointer to Sentinel skill for gate logic

### King reads on demand
- `design-doc-writer` — only when writing design doc
- `arch-doc-writer` — only when writing arch doc
- `imp-plan-writer` — only when Steward's plan needs review

- [ ] Rewrite King system prompt to ≤800 tokens
- [ ] Move all "quality bar" content out of King into the respective skill files
- [ ] Add `## On-demand skills` section to King listing what to read and when

---

## Revised file structure

```
.amtcz/
  core/
    amatsucozy.md          ← King system prompt (≤800 tokens)
  briefs/
    {id}-scout.md          ← Scout writes, King reads, Knight deletes
    {id}-impact.md         ← Scout writes after design, King reads
    {id}-blocker.md        ← Knight writes on 3rd failure, King reads
  checkpoints/
    {id}.md                ← King writes after each phase, used for resume
  templates/
    task-design-template.md
    implementation-plan-template.md
    architecture-doc-template.md

.claude/
  agents/
    king.md                ← King agent (Sonnet) — renamed from orchestrator
    scout.md               ← Scout sub-agent (Haiku)
    steward.md             ← Steward sub-agent (Haiku)
    knight.md              ← Knight sub-agent (Sonnet)
  skills/
    sentinel/
      SKILL.md             ← Gate logic only, ≤300 tokens, cached
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
    source-fast-search/    ← existing, unchanged
      SKILL.md
    source-navigator/      ← existing, unchanged
      SKILL.md
    source-indexer/        ← existing, unchanged
      SKILL.md
    source-analyzer/       ← existing, unchanged
      SKILL.md
      parsers/
```

---

## Token budget estimates (post-fix)

| Scenario | Before | After | Saving |
|---|---|---|---|
| Simple bug fix `*sw` | ~18k | ~8k | 56% |
| Medium feature `*sw --auto` | ~55k | ~22k | 60% |
| Large refactor `*sw --auto` | ~120k+ | ~45k | 63% |
| `*cad` large module | ~40k | ~18k | 55% |

---

## Optimization order

Work in this sequence — each fix unblocks the next:

1. **Brief file schema** — fixes the handoff foundation everything else depends on
2. **Model routing** — highest ROI, independent of other fixes
3. **King context budget** — requires brief schema to be defined first
4. **Knight failure recovery** — requires blocker file schema (part of brief protocol)
5. **Sentinel scope narrowing** — cleanup, depends on King being slimmed first
6. **Scout skill dispatch** — refinement, depends on Scout being well-defined
7. **System prompt size** — final polish, do last to avoid rewriting twice

---

## Files to rewrite

- [ ] `.claude/agents/king.md` — new file, replaces orchestrator.md + design.md
- [ ] `.claude/agents/scout.md` — new file, replaces (none — new addition)
- [ ] `.claude/agents/steward.md` — rewrite of planner.md with Haiku targeting + context discipline
- [ ] `.claude/agents/knight.md` — rewrite of implementer.md with failure recovery
- [ ] `.claude/skills/sentinel/SKILL.md` — rewrite of gate-enforcer with scope split + size trim
- [ ] `.claude/skills/design-doc-writer/SKILL.md` — trim, remove content now in King
- [ ] `.claude/skills/arch-doc-writer/SKILL.md` — trim, verify references still valid
- [ ] `.claude/skills/imp-plan-writer/SKILL.md` — trim, remove content now in Steward
- [ ] `.claude/skills/code-implementer/SKILL.md` — trim, core rules now in Knight
- [ ] `README.md` — update cast, commands, file structure
- [ ] **Delete:** `agents/design.md`, `agents/implementer.md`, `agents/orchestrator.md`, `agents/planner.md`, `agents/doc-writer.md`
- [ ] **Delete:** `skills/ticket-id-assigner/`, `skills/business-doc-writer/`
- [ ] **Keep unchanged:** all four source skills (`source-navigator`, `source-fast-search`, `source-indexer`, `source-analyzer`)
