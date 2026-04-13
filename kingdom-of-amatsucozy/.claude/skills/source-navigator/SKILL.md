---
name: source-navigator
description: Answers any codebase question by traversing the two-level context graph — without grepping or scanning directories. Handles five query types: location lookup ("where does X live"), behavioural explanation ("what does X do"), reverse dependency lookup ("what depends on X"), project start up method ("How to start the project locally?"), and path traversal ("trace the flow from A to B"). Always searches across ALL projects in the graph, returning every location a concept appears — including SDK boundaries and external references. Use this skill automatically whenever a user asks about code location, behaviour, dependencies, or flow in a large codebase. Strongly prefer this over grep or directory scanning whenever .amtcz/context.md exists.
cache_control: ephemeral
---

# Skill: source-navigator

A knowledge assistant for large codebases. Answers questions about where
things live, what they do, what depends on them, and how flows connect —
by reading the context graph, not scanning files.

---

## Pre-Flight Check

Before any query, verify `.amtcz/context.md` exists.

| State | Action |
|-------|--------|
| Missing | Stop. Say: "There's no context map yet. Run `*index` to build one first." |
| Last Updated > 30 days | Warn once, then proceed. Flag gaps as `[POSSIBLY STALE]`. |
| Present | Identify the query mode and begin. |

---

## Query Mode Detection

Classify the user's question into one of four modes before doing anything else.

| Mode | Signal phrases | Example |
|------|---------------|---------|
| **Locate** | "where", "which file", "find", "where does X live" | "Where does the payment feature live?" |
| **Explain** | "what does", "how does", "explain", "what is" | "What does PaymentClient.Charge do?" |
| **Depend** | "what uses", "what depends on", "who calls", "references to" | "What depends on IUserRepository?" |
| **Trace** | "trace", "follow", "flow from A to B", "how does X reach Y" | "Trace the flow from login to token issuance" |

If the question is ambiguous, make your best classification, state it
explicitly, and proceed. Do not ask for clarification upfront — the user
can redirect if wrong.

---

## Mode 1 — Locate

**Goal:** Find every place a concept, class, feature, or method lives
across the entire codebase, including SDK and external boundaries.

### Algorithm

1. **Graph-wide scan:** Read `.amtcz/context.md`. For every indexed project,
   read its `context.md`. Scan the Entity Map and Route Map of each.

2. **Match against all of these simultaneously:**
   - Class / Interface names
   - Method names in the Public Methods column
   - Route paths in the Route Map
   - Project Owns descriptions (for feature-level queries)

3. **Collect every match across all projects.** Do not stop at the first hit.

4. **Check External References** in `.amtcz/context.md`. If any entry's
   description matches the query:
   - Record it as an external hit.
   - Mark it `[EXTERNAL — NOT INDEXED]` if no context.md is linked.
   - Do NOT attempt to traverse into it. Report the boundary.

5. **Output all findings** using the Locate Result format.

### Locate Result Format

```
## Locate: "{query}"

Found {N} location(s) across {M} project(s).

### In-Repo Locations

**{ProjectName}**
| Match | Type | File | Relevant Methods |
|-------|------|------|-----------------|
| PaymentService | Service | /src/core/Services/PaymentService.cs | Charge(request), Refund(id), GetStatus(id) |
| IPaymentService | Interface | /src/core/Interfaces/IPaymentService.cs | Charge(request), Refund(id), GetStatus(id) |

**{AnotherProject}**
| Match | Type | File | Relevant Methods |
|-------|------|------|-----------------|
| PaymentController | Controller | /src/api/Controllers/PaymentController.cs | PostCharge(dto), PostRefund(dto) |
| POST /api/payments/charge | Route | → PaymentController.PostCharge | — |

### SDK / External Locations

| Name | Location | Relevant Methods | Status |
|------|----------|-----------------|--------|
| PaymentClient | @org/payment-sdk | Charge(request), Refund(id) | [EXTERNAL — NOT INDEXED] |

### Open Questions
- {Any [STALE] or [UNRESOLVED] entries encountered}
```

---

## Mode 2 — Explain

**Goal:** Describe what a class or method does, using source files only
when the context map doesn't contain enough information.

### Algorithm

1. Run **Locate** first to find the target. If multiple matches exist,
   list them all and ask the user which one to explain.

2. For each matched entity, read the source file at the recorded path.
   Extract:
   - Method signatures and parameter names
   - Any XML / docstring / JSDoc documentation present
   - The immediate logic of the target method only (not its full call tree)
   - Dependencies injected or imported at the class level

3. If the target is an interface, also find its concrete implementation
   via the Entity Map and read that too.

4. If the target is `[EXTERNAL — NOT INDEXED]`, report only what the
   context map surface: name, location, relevant methods. Do not attempt
   to fetch or inspect the external package.

### Explain Result Format

```
## Explain: "{query}"

### {ClassName}.{MethodName}
**File:** {file_path}
**Project:** {ProjectName}

**What it does:**
{Plain language explanation based on the source, 2-4 sentences.}

**Parameters:**
- {param}: {what it represents}

**Dependencies used:**
- {IServiceName} — {what it does in context of this method}

**Implementation:** {In-repo | External SDK — cannot inspect}
```

---

## Mode 3 — Depend

**Goal:** Find every class, method, or project that references the
target — a reverse dependency lookup.

### Algorithm

1. Run **Locate** to confirm the target exists and get its exact name.

2. Scan the Entity Map of every indexed project. Look for the target
   name in the Public Methods column of other classes — these are callers.

3. Open source files of candidate callers only when the context map is
   ambiguous (e.g., same method name in multiple classes).

4. Check External References — if an external project's description
   references the target, include it as a dependent.

5. Collect all findings. Group by project.

### Depend Result Format

```
## Depends on "{target}": {N} reference(s) found

### {ProjectName}
| Caller | File | Via Method |
|--------|------|-----------|
| UserController | /src/api/Controllers/UserController.cs | GetById(id) |
| UserService | /src/core/Services/UserService.cs | Create(dto) |

### External
| Name | Type | Notes |
|------|------|-------|
| @org/consumer-sdk | External package | References IUserService per External References table |
```

---

## Mode 4 — Trace

**Goal:** Follow the execution path from a start point (A) to an end
point (B), listing every hop in order.

### Algorithm

1. **Locate A** — find the entry point using Mode 1.
2. **Locate B** — find the destination using Mode 1. If B isn't clearly
   defined, ask the user to confirm what "reaching B" looks like.

3. **Walk the chain:**
   - Open the source file for A. Extract dependencies.
   - For each dependency, check the context map to identify its file.
   - Open that file. Extract its dependencies.
   - Repeat until B is reached or an exit condition triggers.

4. **Exit conditions:**

| Condition | Action |
|-----------|--------|
| B is reached | Report the complete chain. Stop. |
| SDK boundary hit | Record: name, file, relevant methods. Stop. Do not cross. |
| Class missing from all context maps | Mark `[STALE]`. Offer to re-index. Continue other branches. |
| 6 hops without reaching B | Pause. Surface chain so far. Ask: "Continue into `{next}`, or is this enough?" |
| Dead end — no further dependencies | Report: "Chain ends here without reaching B. Try another branch?" |

### Trace Result Format

```
## Trace: "{A}" → "{B}"

### Path ({N} hops)

1. **{ProjectA}** → {ClassA}.{MethodA} — `{file_path}`
   ↓ calls
2. **{ProjectB}** → {ClassB}.{MethodB} — `{file_path}`
   ↓ calls
3. **[SDK BOUNDARY]** → {SDKName}.{MethodName}
   Relevant methods: {MethodName(params)}
   Location: {package name or repo URL}
   Status: [EXTERNAL — NOT INDEXED]

### Summary
{Plain language summary of what the chain does and where it ends.}

### Open Questions
- {Unresolved entries, stale index warnings, unexplored branches}
```

---

## Hard Rules

- **Never grep. Never scan.** Only open files with a specific path from
  the context graph.
- **Always search all projects.** Never stop at the first match. A concept
  may live in multiple projects — all must be reported.
- **SDK boundary = stop and report.** Never traverse into an external
  package. Surface name, relevant methods, and mark `[EXTERNAL — NOT INDEXED]`.
- **Missing from context = stale, not absent.** If a class isn't in any
  context.md, say the map may be stale and offer `*index {project}`.
  Never scan for it.
- **One question at a time.** If clarification is needed mid-traversal,
  ask only the most blocking question.
- **Hop limit is a pause, not a failure.** Surface findings and ask for
  direction. Never silently abandon a trace.
