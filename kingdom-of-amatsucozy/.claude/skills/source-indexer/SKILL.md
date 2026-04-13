---
name: source-indexer
description: Builds and maintains a navigable two-level context graph for any codebase. Creates a master map at .amtcz/context.md (listing all projects and their plain-language responsibilities) and per-project context.md files (listing every public class, its public methods, and all HTTP routes). Use this skill whenever the user wants to index a project, set up AI navigation for a repo, refresh a stale map, or says anything like "index this", "build context", "map the codebase", "update the context map", or "re-index". Also trigger automatically when source-navigator reports a [STALE] or [MISSING] entry during traversal.
cache_control: ephemeral
---

# Skill: source-indexer

Builds the two-level context graph that lets AI navigate a codebase by
following a map rather than scanning files or grepping.

See `references/schemas.md` for the exact output schemas for both
context.md levels.

---

## When to Run

- First-time setup — no `.amtcz/context.md` exists yet
- A new project was added to the repo
- source-navigator hit a `[STALE]` or `[MISSING]` entry
- User requests a refresh: `*index` or `*index [project_name]`

---

## Procedure

### Step 1 — Determine Scope

Check for `.amtcz/context.md`.

**If it exists:** Read the Project Map table.
- If `project_name` was given: index that project only, even if already indexed.
- If no name given: find the first row marked `[NOT INDEXED]` and select it.
- If all rows are indexed: report "All projects are indexed. Provide a project
  name to force a refresh." and stop.

**If it does not exist:** Scan the repo root for project markers:
`*.csproj`, `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`,
`*.sln`, `pyproject.toml`.
List every discovered project root. Select the first alphabetically unless
`project_name` was given.

**If the user provided an explicit path** (e.g., `/src/api` or `./worker`):
Treat that path as the target directly — skip marker discovery entirely.
Validate the path exists before proceeding. If it does not exist, stop and
tell the user: "I couldn't find a directory at `{path}`. Please check the path
and try again."

Notify the user: "Indexing `{target_project}`."

---

### Step 2 — Extract Entities

Scan every source file in the target project. For each file, extract:

**Classes & Interfaces**
Every `public class`, `public interface`, `public record`, `export class`,
`export interface`, `export type` (TypeScript), or top-level Python `class`.
For each one:
- Its file path (relative to repo root)
- Its layer (see Layer Taxonomy below)
- Every public method: name + parameter names only, no return types

**Routes**
Detect HTTP route bindings regardless of framework:
- C#/.NET: `[HttpGet]`, `[HttpPost]`, `[HttpPut]`, `[HttpDelete]`,
  `[Route(...)]` attributes
- Python: `@app.get(...)`, `@router.post(...)`, `@blueprint.route(...)`
- TypeScript/Node: `router.get(...)`, `app.post(...)`, `@Get(...)`, `@Post(...)`
- Angular: `RouterModule` path definitions (these go in a Routes section,
  not a Route Map)

Map each route: `METHOD /path → ClassName.MethodName`

**Layer Taxonomy**
Assign one layer label per class. Use the most specific match:

| Label | Identifies |
|-------|-----------|
| `Controller` | Handles HTTP requests |
| `Service` | Business logic |
| `Repository` | Data access / persistence |
| `Interface` | Contract / abstraction |
| `Model` | DTOs, domain entities, data shapes |
| `Worker` | Background jobs, queue consumers |
| `Middleware` | Cross-cutting concerns, filters, guards |
| `Config` | Configuration, startup, DI registration |
| `Utility` | Helpers with no layer affiliation |

If a class spans multiple layers (e.g., a Controller with embedded business
logic), use the most specific label and append ` ⚠️ mixed` to the class name
in the Entity Map.

---

### Step 3 — Write Project-Level context.md

Write to `/{project_path}/context.md`. Load and follow the schema in
`references/schemas.md` → **Project-Level Schema**.

Key rules:
- Rows must be sorted by Layer, then alphabetically by class name.
- If a class has no public methods, write `—` in the Methods column.
  Do not omit the row.
- If a route's handler class cannot be determined, write `[UNRESOLVED]`
  in the Handler column.

---

### Step 4 — Update Master context.md

Update or create `.amtcz/context.md`. Load and follow the schema in
`references/schemas.md` → **Master Schema**.

**Writing the Owns column:**
This is the most important field — it's how source-navigator identifies
the right project from a symptom. Write 3–6 plain-language phrases
covering the project's actual responsibilities. Think: what would a
developer say this project "owns"?

Good: `HTTP endpoints, user auth routes, request validation, API versioning`
Bad: `API project` or `handles requests`

**External References:**
Include this table only if cross-repo dependencies are detected:
private NuGet feeds, npm org-scoped packages (`@org/package`),
Git submodules, or explicit repo URLs in config files.

---

## Hard Rules

- **Zero inference.** List only what is explicitly present in source.
  Do not guess responsibilities, method signatures, or layer assignments.
- **Unresolved over invented.** When uncertain, write `[UNRESOLVED]`
  or `[UNKNOWN]` — never fabricate a value.
- **Stale, not deleted.** If a previously indexed project's path no longer
  exists on disk, mark it `[REMOVED]` in the master map. Never delete rows.
- **No grepping.** Read files directly. Do not issue shell search commands
  to discover entities.
- **Owns must be human-readable.** The Owns column is read by an AI matching
  plain language. Avoid abbreviations, internal codenames, or jargon.
