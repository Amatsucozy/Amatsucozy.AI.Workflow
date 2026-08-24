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
   `amtcz-mcp` server is registered/reachable in that context; a subagent
   that finds the tools unavailable reports `blocked` — the degraded-mode
   decision belongs to the human via the main thread, never to a subagent.

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
