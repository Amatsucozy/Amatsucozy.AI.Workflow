# Experience-First Task Routing (always applies)

Durable lessons live in `docs/experiences/*.md`. Before ANY investigation,
implementation, refactor, debugging, or technology decision, you MUST run this
routing — it is a required step, not a suggestion. It runs once you know what
you're solving, never before: don't fire the inventory on a bare greeting or
an unparsed human message, and don't fire it while you're still mid-intake
clarifying scope. The "unconditional" language in step 2 is about not
skipping the search once a task exists — it is not license to run tooling
before one does.

1. State the problem in one sentence before touching any tooling. Read (or,
   if intake is incomplete, ask for) what you're actually trying to solve —
   the symptom, the feature, the question. If you can't state it yet, you're
   not ready for step 2; get it from the human or the ticket first.
2. Run the tag inventory — unconditionally, every task, once step 1 is
   satisfied, before deriving anything else: call the `exp_inventory` MCP
   tool (no params needed, `root` defaults to `.`).
   Not gated on "if unsure" — self-assessed confidence is exactly what
   fails here; a tag you invented to fit the task sounds no less plausible
   to you than one actually grounded in the corpus, so that check never
   fires. `verdict == "no_entries"` (no entries yet) → skip straight to
   step 6, FRESH problem.
3. Derive 2–4 search terms from the task, matched against the tag list you
   just saw: technology names, error fragments, domain concepts. Prefer an
   inventory tag over a same-meaning invented one — inventory shows
   `dependency-injection`, not your first-instinct `di`; search on the
   former. This rule is about the `tag` parameter specifically: `symptom`
   and `keyword` are free text and are not required to pre-exist in the
   inventory.
4. Find candidates and confirm their trigger in a single call — pass
   whichever of `tag` / `symptom` / `keyword` fit, all combined in one call
   to the `exp_search` tool (`tag` and `keyword` are lists, `symptom` is a
   single string — same names, same semantics as before).
   About to call `exp_search` with a `tag` without having run step 2 in
   this task? Stop, run step 2, then come back — that shortcut is the
   exact failure this routing exists to prevent.
   The report's Use-When column is the fit check: an entry is a match only
   if Use-When describes the situation you are in. A high match count or
   tag/keyword overlap alone is not a match; do not judge from filenames.
5. One or more confirmed → HISTORICAL problem: read the matching files (most
   specific first, others only if they bear on the same task) and apply their
   guidance BEFORE any new investigation or code changes.
6. None confirmed → FRESH problem: proceed with normal investigation. Do not
   force unrelated entries into context.
7. Scan the installed skill listing.
   Invoke EVERY skill whose description matches the current task — skills compose;
   loading one does not preclude another.
   A task may legitimately need source-navigator + dotnet-unit-testing together.
   Cite by name any skill you considered and deliberately skipped.
8. Any decision that relies on an entry — or deliberately overrides one — must
   cite it by slug.
9. If a fresh problem's solution is likely to help again in this repository,
   invoke the `experiences` skill to capture it before closing the task.
10. Subagents do NOT inherit this routing — their context starts empty. When
   spawning a subagent of any kind, attach the confirmed-relevant entries'
   Lesson and Applies When/Not When sections (with slugs) directly in the
   dispatch prompt. Attach only confirmed matches, never unconfirmed
   candidates. The tools resolve for subagent calls too as long as the
   relevant server (`amtcz`, `dbschema`, `roslyn`) is registered/reachable
   in that context; a subagent that finds a tool it needs unavailable
   reports `blocked` — the degraded-mode decision belongs to the human via
   the main thread, never to a subagent.

---

## Reference — amtcz-mcp tools

The 6 tools (`sarif_build`, `sarif_probe`, `test_run`, `test_probe`,
`exp_inventory`, `exp_search`) are self-describing — once the `amtcz-mcp`
server is registered, the agent sees each tool's name, parameters, and full
description (including what every `verdict` value means) directly in its
tool list. This reference exists only for judgment calls that live ACROSS
tools, not inside any single tool's own description.

### Quick Reference — by scenario

Match the situation you're actually in, call that tool, done. Each tool's
own docstring explains *why* and lists every parameter/verdict in full;
this table exists so cross-tool judgment calls don't have to be re-derived
every time.

**Build**

| Scenario | Tool call |
|---|---|
| Routine build at a gate / "does it compile" | call `sarif_build` |
| Just built, error table got truncated | call `sarif_probe` with a larger `max_rows` — **not** another `sarif_build` |
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
| Just ran tests, failure table got truncated | call `test_probe` with a larger `max_rows` — **not** another `test_run` |
| Re-verifying one or a few specific tests after a fix | call `test_run` with `no_build=true` and `filter="<expr>"` |
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

The 7 tools (`catalog_info`, `catalog_refresh`, `schema_search_tables`,
`schema_search_columns`, `schema_describe_table`, `schema_related_tables`,
`schema_list_tables`) are self-describing — once the `dbschema` server is
registered, the agent sees each tool's name, parameters, and full description
(including what every `verdict` value means) directly in its tool list. This
reference exists only for judgment calls that live ACROSS tools, not inside
any single tool's own description.

**The server returns structure, never rows.** No tool executes a query against
user tables. SQL authorship stays with the agent — which is why reading
`hints` is not optional.

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
| `related` returned `no_relations` | the schema may declare no FK constraints at all — infer join columns by name from `schema_describe_table`, don't conclude the tables are unrelated |
| Tempted to raise `depth` above 1 | only when a direct join genuinely doesn't reach the entity; depth 3+ on a normalised schema returns most of the database |

**Failure**

| Scenario | Tool call |
|---|---|
| `verdict == "catalog_unavailable"` | environment/config problem (`DBSCHEMA_URL` unset, driver missing, connection refused) — see `error`, surface it to the human. Every tool returns this until it's fixed; calling a different tool will not help |
| Any tool needs a connection string | it doesn't — credentials are environment-only, by design. Never put one in a tool parameter |

---

## Reference — roslyn-mcp tools

The 9 tools (`workspace_status`, `document_symbols`, `definition`,
`implementations`, `references`, `hover`, `diagnostics`, `rename_preview`,
`refresh_file`) are self-describing — once the `roslyn` server is registered,
the agent sees each tool's name, parameters, and full description directly in
its tool list. This reference exists only for judgment calls that live ACROSS
tools, not inside any single tool's own description.

**Semantic, not textual.** Every answer comes from the live Roslyn workspace
(the same engine as VS Code's C# extension), not from grep — a `references`
result is the true call graph, and `rename_preview` computes but never
applies. All line/column values are 1-based. Every result carries `verdict`:
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
| First C# semantic question of the session | call `workspace_status(wait_seconds=120)` — pays the project-load cost once; the server stays warm afterwards |
| Any tool returned `verdict == "workspace_loading"` | poll `workspace_status` until `ready: true`, then repeat the **same** call. An empty result under this verdict is not an answer |
| Any tool returned `verdict == "workspace_unselected"` | the file could be owned by several solutions (or none) — call `workspace_status(solution=<one of candidates>)`, then repeat the **same** call. Later ambiguous files follow that selection. Set `ROSLYN_MCP_SOLUTION` in the server config to pin one permanently |
| Multi-repo root, want to pre-load one repo's solution | call `workspace_status(solution="<repo>/<X>.sln", wait_seconds=120)`; `workspace_status.workspaces` lists every loaded process (LRU-capped by `ROSLYN_MCP_MAX_WORKSPACES`, default 2) |
| `verdict == "server_dead"` | call `workspace_status` once — it restarts Roslyn. If it dies again, surface `log_dir` (`.roslyn-mcp/<sln-stem>/roslyn-stderr.log`) to the human; don't loop |
| `verdict == "file_not_found"` | the path is wrong (relative paths resolve against the server root, not the shell cwd) — fix the path, don't retry as-is |
| `verdict == "timeout"` | first request after start on a large solution — re-check `workspace_status`, then retry once |

**Finding things**

| Scenario | Tool call |
|---|---|
| Know the file, need a line/col to pass to another tool | call `document_symbols` first — never guess positions |
| Need a resolved type or full signature | call `hover` — cheaper than `definition` plus a Read |
| "Where is X defined?" | call `definition`; empty `locations` with `ok` means the position isn't a resolvable symbol, or it's metadata-only (BCL) |
| "Who implements / overrides X?" (interface, abstract, virtual) | call `implementations`, not `references` — `references` returns usages, not implementers |
| "Who calls / what uses X?" | call `references`; `total == 0` with `ok` is a real answer. `truncated: true` → re-call with a larger `max_results`, don't paginate by hand |
| Location/behaviour/dependency question and `.amtcz/context.md` exists | `source-navigator` first — it answers "which project / which class" from the graph. Come to roslyn for exact positions, private members, and the precise reference set the graph can't answer |

**Editing**

| Scenario | Tool call |
|---|---|
| Just edited a file on disk, about to query it | call `refresh_file` first — Roslyn holds the document open and won't see the change otherwise (`diagnostics` refreshes implicitly) |
| Quick per-file compile check after an edit | call `diagnostics` — no build. **Not a gate**: whole-solution verdicts still come from `sarif_build` |
| Renaming a symbol | call `rename_preview`, review `by_file`, then apply the edits yourself — nothing on disk is touched by the tool |
