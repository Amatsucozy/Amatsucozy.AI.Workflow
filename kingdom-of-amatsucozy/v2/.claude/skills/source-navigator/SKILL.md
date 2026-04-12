---
name: source-navigator
description: Traverses the two-level context graph to locate the root cause of a reported issue — following the dependency chain from a symptom (broken endpoint, failing feature, unexpected behavior) through controllers, services, and repositories without grepping or scanning directories. Use this skill automatically whenever a user reports a bug, asks "where does X happen", "which file handles Y", "why is endpoint Z broken", "trace this for me", or any question that requires following a code path through a layered architecture. Strongly prefer this over grep or recursive directory scanning whenever .amtcz/context.md exists.
---

# Skill: source-navigator

Traces a code path through the context graph — alternating between context.md
files (navigation) and source files (dependency confirmation) — until the
fault location is isolated or a decision point is reached.

---

## Pre-Flight Check

Before any traversal, verify `.amtcz/context.md` exists and is readable.

| State | Action |
|-------|--------|
| Missing | Stop. Tell the user: "There's no context map yet. Run `*index` to build one first." |
| Last Updated > 30 days | Warn the user, then proceed. Flag any gap found as `[POSSIBLY STALE]` rather than a hard error. |
| Present and fresh | Begin traversal. |

---

## Traversal Algorithm

Traversal alternates between two modes:

- **Navigate** — read a context.md to identify a file
- **Confirm** — open that file to extract its dependencies

Never scan directories. Never grep. Follow the graph or stop.

---

### Hop 1 — Identify the Owning Project (Navigate)

Read `.amtcz/context.md` → Project Map.

Match the user's symptom against the **Owns** column using plain language.
Examples:

| Symptom | Owns match |
|---------|-----------|
| "GET /api/users/{id} is broken" | project that owns HTTP endpoints |
| "emails are not sending" | project that owns email dispatch |
| "login always returns 401" | project that owns auth routes |
| "PDF export is failing" | project that owns PDF export |

**If one project matches clearly:** proceed.
**If multiple projects could match:** list them and ask the user to confirm.
Do not guess.

→ Record: `owning_project`, `project_context_path`

---

### Hop 2 — Find the Entry Point (Navigate)

Read `{project_context_path}`.

**If the user named a specific route** (e.g., `GET /api/users/{id}`):
→ Match directly against the Route Map.
→ Record: `handler_class`, `handler_method`, `file_path`

**If the project has no Route Map** (pure service/library project):
→ The project is not an HTTP entry point. Return to `.amtcz/context.md`
  and re-evaluate — the entry point likely lives in a different project.
  Tell the user: "The `{project}` project has no HTTP routes — it's likely
  a downstream dependency. Let me look for the entry point in another project."
  Then re-run Hop 1 with more specificity.

**If the user described a feature** (e.g., "the user creation flow"):
→ Scan the Entity Map's Public Methods column for matching method names.
→ If multiple candidates, list them and ask the user to confirm.

**If Route Map has `[UNRESOLVED]` for the matched route:**
→ Tell the user: "The route exists in the index but its handler isn't
  mapped. The context may be stale — run `*index {project}` to refresh."
→ Stop traversal.

---

### Hop 3 — First Source Read (Confirm)

Open `{file_path}`.

Read only the minimum needed to extract dependencies. What "dependency" means
varies by language — look for all of these:

| Pattern | Language |
|---------|----------|
| Constructor parameters typed as interfaces/classes | C#, Java, TypeScript |
| `@Injectable` / `@Inject` decorated params | Angular, NestJS |
| Module-level `import` of service classes | Python, Node.js |
| `__init__` parameters | Python |
| `private readonly` / `private` field declarations | C#, TypeScript |
| `services.GetService<T>()` calls | C# service locator |

Record every external class or interface this file depends on.
Do NOT read full method implementations. You are mapping the graph, not
debugging the logic.

→ Record: `dependencies[]` — list of interface/class names this file depends on

---

### Hop N — Resolve Dependencies (Navigate → Confirm loop)

For each unresolved dependency in the queue:

1. **Navigate:** Return to `.amtcz/context.md`.
   Find which project's Owns column best matches the dependency's domain.
   Read that project's `context.md` → Entity Map.
   Find the class and its file path.

2. **Confirm:** Open that source file.
   Extract its dependencies. Add new ones to the queue.

3. Check exit conditions after each hop:

| Condition | Action |
|-----------|--------|
| A method with no further unresolved dependencies | Mark as **likely fault location**. Report findings. |
| A dependency marked `[NOT LINKED]` in External References | Surface as **external blind spot**. Ask user if they want to inspect that repo manually. |
| A class is missing from all context.md files | Mark as `[STALE]`. Tell the user: "I can't find `{ClassName}` in the index. Run `*index` to refresh, or open the file manually." |
| 5 hops completed | **Pause.** Surface current findings. Ask: "Should I continue deeper into `{next_dependency}`, or does this give you enough to investigate?" |
| User says stop | Report the traversal chain so far and the current open questions. |

---

## Output Format

Report findings at any exit point using this structure:

```
## Navigation Result

**Symptom:** {user's original description}
**Entry Point:** {ClassName.MethodName} → {file_path}

### Traversal Chain
1. {ProjectA} → {ClassA} → {file_path_a}
2. {ProjectB} → {ClassB} → {file_path_b}
3. ...

### Likely Fault Location
**File:** {file_path}
**Class:** {ClassName}
**Method:** {MethodName}
**Reason:** {one sentence — why this is the likely fault point}

### Open Questions
- {Any [STALE], [UNRESOLVED], or [NOT LINKED] entries encountered}
- {Any decision points the user should confirm}
```

If the traversal was paused at the hop limit, add a **Next Steps** section:

```
### Next Steps
To continue: I would follow `{ClassName}` into `{ProjectX}`.
Say "continue" to proceed, or point me to a specific dependency.
```

---

## Hard Rules

- **Never grep.** Never scan directories. Never list files. Only open files
  you have a specific path for from the context graph.
- **One file at a time.** Read source files only to extract dependencies —
  not to speculatively explore implementations.
- **Never guess a project.** If the Owns column doesn't clearly match
  the symptom, ask the user before proceeding.
- **Hop limit is a pause, not a failure.** At 5 hops, surface current
  findings and ask for direction. Do not abandon the traversal or restart.
- **Missing context = re-index prompt.** If a class isn't in context.md,
  do not scan for it. Tell the user the map is stale and offer to re-index.
- **One question at a time.** If you need clarification, ask the most
  important question only. Do not present a list of questions.
