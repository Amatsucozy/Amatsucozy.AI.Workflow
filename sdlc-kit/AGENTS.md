# Codex SDLC Project Instructions

Resolve `docs/experiences/` and `docs/tasks/` relative to the target project root.

## Codex Working Conventions

- User instructions and existing authorization take precedence over these
  workflow conventions. Continue authorized work; ask only for material
  missing information or an action that still requires approval.
- Read applicable skills from the available skill listing or
  `.agents/skills/<name>/SKILL.md`.
  Load skills whose actual workflow fits the request; do not start a full
  SDLC pipeline for an ordinary edit or question merely because it uses tools.
- For an end-to-end pipeline request, use
  [sdlc-orchestrator](.agents/skills/sdlc-orchestrator/SKILL.md), with
  [requirements](.agents/skills/requirements/SKILL.md),
  [planning](.agents/skills/planning/SKILL.md), and
  [reporting](.agents/skills/reporting/SKILL.md) at their respective stages.
  Task state lives in `docs/tasks/<id>/main.yaml`.
- Read agent definitions from `.codex/agents/`. Dispatch only when requested or
  required by the active workflow and permitted by the runtime. Pass the
  role's inputs explicitly; model and reasoning effort inherit from the
  session. File instructions do not enforce tool allowlists or grant access.
- Use `rg --files`, `rg -n`, and targeted file reads through available shell
  tools. Adapt syntax to PowerShell or POSIX as appropriate. Batch independent
  reads/searches and keep dependent operations and edits sequential.
- Discover configured MCP operations using the available tool listing or
  tool search. Server prefixes vary; match the server and operation, then
  inspect its actual schema. The operation names below are not guaranteed
  fully qualified Codex tool names.
- Confirm the tools' project root when it differs from the shell working
  directory; pass the appropriate `root` or file path instead of assuming
  `.` always points at the target project.

## Experience-First Task Routing

Durable lessons live in `docs/experiences/*.md`. Run this routing once the
problem is known and before investigation, implementation, refactoring,
debugging, or a technology decision. Do not run it on greetings or while
intake still lacks a defined problem. Repeat searches when a new failure
introduces different symptoms; reuse confirmed matches within the same task.

1. State the problem in one sentence, using the request and available context.
   Ask only if the missing information prevents identifying the task. Then
   name the task's concerns: `implementation` always, and `tests` whenever
   the work adds, changes, or fixes tests — an AC names tests, a test file
   is in scope, or a test is what failed. Route each concern separately: a
   single pass on the implementation problem retrieves no test lessons.
2. Call `exp_inventory` before choosing tags (`root` defaults to `.`; pass the
   target project root if necessary). This inventory is required even when
   confident about the likely lesson. `verdict == "no_entries"` means there
   are no entries to search; proceed with a fresh investigation.
3. Derive 2–4 terms per concern from the task and inventory: technologies,
   error fragments, and domain concepts — for `tests`, the test framework,
   mocking and assertion libraries, fixture and naming patterns, and the
   `test`-family tags the inventory shows. Prefer existing tags over invented
   synonyms. `symptom` and `keyword` are free text and need not appear in
   the inventory.
4. Call `exp_search` once per concern with that concern's `tag` / `symptom` /
   `keyword` filters together (a mixed call ranks by tag weight under a
   `max_rows` cap, so the larger concern crowds out the smaller). `tag` and
   `keyword` are lists; `symptom` is a string. Confirm candidates against the
   report's Use-When column — for `tests`, the situation is writing or fixing
   the tests, not changing the code under test. Tag overlap or a filename
   alone does not establish relevance.
5. Read confirmed matches, most specific first, and apply relevant guidance
   before new investigation or edits. If none fits, proceed without loading
   unrelated lessons. Cite the slug when relying on or overriding a lesson.
   Declare the outcome per concern — matched slugs, or "no experience match
   (tests)"; a `tests` concern with no declaration has not finished routing.
6. Use the applicable installed skills for the task. At close, use
   [experiences](.agents/skills/experiences/SKILL.md) if an evidence-backed
   finding would help future work; update an existing lesson when it already
   covers the finding.
7. When delegating, attach confirmed entries' Lesson and Applies When/Not When
   sections with their slugs, matched to the delegate's concern: a phase that
   writes or fixes tests carries the `tests` lessons, an implementation phase
   the `implementation` ones, a phase doing both carries both. Do not assume
   the child inherited the parent's searches, file reads, or MCP
   availability. A worker reports a missing required capability to the
   parent without claiming the check ran.

If the experience tools are unavailable, inspect the local entries with `rg`:
first inventory their `tags:` fields, then search tags, `symptom:`, and
`use-when:` and read candidates to confirm relevance. This is the supported
experience-routing fallback. A missing directory or no confirmed matches
means no experience match; an unreadable directory is an access gap, not
proof that no lessons exist. Report the gap and continue unaffected work.
This fallback does not replace mandatory build/test tools or semantic evidence.

---

## Reference — amtcz-mcp tools

Use [run-build](.agents/skills/run-build/SKILL.md) and
[run-test](.agents/skills/run-test/SKILL.md) for execution and report contracts.
In the full pipeline, those operations belong to reviewer gates unless the
user explicitly requests a main-thread run. Preserve the tools' verdicts and
capped structured reports; do not load raw build/test logs. If required tools
are missing, report the blocked check rather than substituting raw commands.

### Quick Reference — by scenario

**Build**

| Scenario | Tool call |
|---|---|
| Routine build at a gate / "does it compile" | call `sarif_build` |
| Just built, error table got truncated and the user requests more rows | call `sarif_probe` with a larger `max_rows` — **not** another `sarif_build` |
| Need warnings too, not just errors | pass `warnings=true` to whichever of the two above you're already calling |
| Suspect stale/carried logs — branch switch, a project was removed from the solution, or the human explicitly asked for a clean build | call `sarif_build` with `rebuild=true` — human-request only |
| `verdict == "no_sarif_logs"` | infrastructure problem, not a param problem — report the console tail; don't retry with different params |
| `verdict == "gap_msbuild_failure"` | MSBuild-level failure (restore/SDK/references), not a compiler error — report the console-tail line; calling `sarif_probe` won't find errors that were never written |
| `verdict == "dotnet_not_found"` | environment problem — surface to the human, don't retry |

**Test**

| Scenario | Tool call |
|---|---|
| Tests right after a successful build, same gate | call `test_run` with `no_build=true` |
| Running tests without a build earlier this session | call `test_run` (omit `no_build`) |
| Just ran tests, failure table got truncated and the user requests more rows | call `test_probe` with a larger `max_rows` — **not** another `test_run` |
| Re-verifying one or a few specific tests after a fix | call `test_run` with the authorized `filter="<expr>"`; use `no_build=true` only after building the changed inputs |
| `verdict == "no_trx"` | host crash or logger/results-dir mismatch — report the console tail, don't retry blind |
| `verdict == "zero_discovered"` | bad `filter` or wrong target — fix the invocation once, don't loop |
| `verdict == "dotnet_not_found"` | environment problem — surface to the human, don't retry |

**Experience routing**

| Scenario | Tool call |
|---|---|
| Start of any task (routing step 2) | call `exp_inventory` |
| Tags/symptom/keywords derived, need candidates (routing step 4) | call `exp_search` with `tag`/`symptom`/`keyword` |
| `exp_inventory` returned `verdict == "no_entries"` | skip search entirely — FRESH problem, per routing step 2 |

---

## Reference — dbschema-mcp tools

Database tools return schema structure, not rows. Read `catalog_info.hints`
before writing SQL.

### Quick Reference — by scenario

**Orientation**

| Scenario | Tool call |
|---|---|
| First database question of the session | call `catalog_info` — read `hints` before writing any SQL (quoting, default schema, `TOP` vs `LIMIT`, concat operator) |
| A migration ran during this session | call `catalog_refresh` |
| Results contradict what the database evidently has | call `catalog_refresh` once — if it still disagrees, the schema filter (`DBSCHEMA_SCHEMAS`) is the likelier cause than a stale snapshot |
| Ordinary lookups, nothing changed | do **not** refresh — the snapshot is taken once per process and is valid for the whole session |

**Finding things**

| Scenario | Tool call |
|---|---|
| "What table holds X?" | call `schema_search_tables` with the domain word |
| "What is the column for Y?" | call `schema_search_columns`; add `table=` once you know the table |
| `verdict == "no_match"` on a search | try a different domain word once, then call `schema_list_tables` — do not keep re-phrasing the same guess |
| Need to eyeball the whole namespace | call `schema_list_tables` (with `schema=`/`kind=` to narrow) — not as a first move on a large database |
| `verdict == "ambiguous"` / `"table_ambiguous"` | re-call with one of the returned `candidates`, which are already schema-qualified |
| `verdict == "not_found"` / `"table_not_found"` | the name is wrong, not the call — find the real name via search/list before retrying |

**Writing the query**

| Scenario | Tool call |
|---|---|
| About to write SQL against a table | call `schema_describe_table` — this is the authoritative column list; never write columns from search hits, which report only what matched |
| Need to join two entities | call `schema_related_tables` and use its `join_on` predicates verbatim; `path` chains them for multi-hop |
| `related` returned `no_relations` | the schema may declare no FK constraints at all — inspect `schema_describe_table` for candidate join columns and label the join as inferred until verified; do not conclude the tables are unrelated |
| Tempted to raise `depth` above 1 | only when a direct join genuinely doesn't reach the entity; depth 3+ on a normalised schema returns most of the database |

**Failure**

| Scenario | Tool call |
|---|---|
| `verdict == "catalog_unavailable"` | environment/config problem (`DBSCHEMA_URL` unset, driver missing, connection refused) — see `error`, surface it to the human. Every tool returns this until it's fixed; calling a different tool will not help |
| Any tool needs a connection string | it doesn't — credentials are environment-only, by design. Never put one in a tool parameter |

---

## Reference — roslyn-mcp tools

`references` identifies semantic usages within the selected solution.
`rename_preview` computes edits without applying them. All line/column values are 1-based. Every result carries `verdict`:
`ok | workspace_loading | workspace_unselected | file_not_found | server_error | server_dead | timeout`.

**One Roslyn process per solution.** The server root may hold several
repositories; each tool maps its `file` to the nearest directory (walking up
to the root) with exactly one `.sln`/`.slnx` and answers from that solution's
process — no need to know which solution a file belongs to. Every semantic
result names the `solution` it came from. `references` never crosses
solutions.

### Quick Reference — by scenario

**Orientation**

| Scenario | Tool call |
|---|---|
| First C# semantic question of the session | call `workspace_status(wait_seconds=30)` — starts or checks project loading; follow the bounded loading rule below if needed |
| Any tool returned `verdict == "workspace_loading"` | poll `workspace_status(wait_seconds=30)` for up to 120 seconds total, then repeat the **same** call if `ready: true`. If still loading, report the unavailable check; an empty result under this verdict is not an answer |
| Any tool returned `verdict == "workspace_unselected"` | the file could be owned by several solutions (or none) — call `workspace_status(solution=<one of candidates>)`, then repeat the **same** call. Later ambiguous files follow that selection. Set `ROSLYN_MCP_SOLUTION` in the server config to pin one permanently |
| Multi-repo root, want to pre-load one repo's solution | call `workspace_status(solution="<repo>/<X>.sln", wait_seconds=30)`; `workspace_status.workspaces` lists every loaded process (LRU-capped by `ROSLYN_MCP_MAX_WORKSPACES`, default 2) |
| `verdict == "server_dead"` | call `workspace_status` once — it restarts Roslyn. If it dies again, surface `log_dir` (`.roslyn-mcp/<sln-stem>/roslyn-stderr.log`) to the human; don't loop |
| `verdict == "file_not_found"` | the path is wrong (relative paths resolve against the server root, not the shell cwd) — fix the path, don't retry as-is |
| `verdict == "timeout"` | first request after start on a large solution — re-check `workspace_status`, then retry once |

**Finding things**

| Scenario | Tool call |
|---|---|
| Know the file, need a line/col to pass to another tool | call `document_symbols` first — never guess positions |
| Need a resolved type or full signature | call `hover` — cheaper than `definition` plus a file read |
| "Where is X defined?" | call `definition`; empty `locations` with `ok` means the position isn't a resolvable symbol, or it's metadata-only (BCL) |
| "Who implements / overrides X?" (interface, abstract, virtual) | call `implementations`, not `references` — `references` returns usages, not implementers |
| "Who calls / what uses X?" | call `references`; `total == 0` with `ok` is a real answer. `truncated: true` → re-call with a larger `max_results`, don't paginate by hand |
| Concept-level question in a multi-project repo ("where does payment live?") | read the `## Project Map` section of the repo's `AGENTS.md` if it has one (a `Project \| Path \| Owns` table) to pick the project, then `rg --files` / `rg` for the symbol, then roslyn for positions, callers, and implementers — roslyn has no workspace-wide symbol search, so the file always comes from `rg --files` / `rg` first |

**Editing**

| Scenario | Tool call |
|---|---|
| Just edited a file on disk, about to query it | call `refresh_file` first — Roslyn holds the document open and won't see the change otherwise (`diagnostics` refreshes implicitly) |
| Quick per-file compile check after an edit | call `diagnostics(min_severity="error")` — no build. Engineer: mandatory on every changed .cs before handoff. Reviewer: mandatory prefilter before `run-build`; a `CS` error skips the build. **Not a gate on its own**: per-file only, callers elsewhere are invisible; whole-solution verdicts still come from `sarif_build` |
| Changed a public/internal signature | call `references` on the member before handoff — callers outside your scope are a Handoff item, not an edit |
| Renaming a symbol | call `rename_preview`, review `by_file`, then apply the edits yourself — nothing on disk is touched by the tool |
