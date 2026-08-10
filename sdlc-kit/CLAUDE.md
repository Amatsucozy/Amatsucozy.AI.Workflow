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
   satisfied, before deriving anything else:
   `amtcz exp inventory`
   Not gated on "if unsure" — self-assessed confidence is exactly what
   fails here; a tag you invented to fit the task sounds no less plausible
   to you than one actually grounded in the corpus, so that check never
   fires. Exit 2 (no entries yet) → skip straight to step 6, FRESH problem.
3. Derive 2–4 search terms from the task, matched against the tag list you
   just saw: technology names, error fragments, domain concepts. Prefer an
   inventory tag over a same-meaning invented one — inventory shows
   `dependency-injection`, not your first-instinct `di`; search on the
   former. This rule is about `--tag` specifically: `--symptom` and
   `--keyword` are free text and are not required to pre-exist in the
   inventory.
4. Find candidates and confirm their trigger in a single call — pass
   whichever of `--tag` / `--symptom` / `--keyword` fit, all combined in one
   invocation:
   `amtcz exp search --tag <tag> --symptom "<error fragment>" --keyword "<broad term>"`
   About to type `--tag` without having run step 2 in this task? Stop, run
   step 2, then come back — that shortcut is the exact failure this
   routing exists to prevent.
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
   candidates. `amtcz` is on the machine PATH, so it resolves for subagent
   Bash calls too; a subagent that finds it absent reports `blocked` — the
   degraded-mode decision belongs to the human via the main thread, never
   to a subagent.

---

## Reference — `amtcz` CLI

`amtcz` is guaranteed installed on PATH — no fallback branch, no
probe-and-STOP gate, no degraded mode anywhere in this kit. This is the full
command reference, inlined always-on (see TUNING.md for why — this used to
be an on-demand skill; it was folded in after observed command misuse). If a
documented flag below is ever rejected, run `amtcz --version` first — that
means the installed CLI predates this doc; upgrade per `amtcz-cli/README.md`.

Shared behavior across every subcommand: all output is pure ASCII,
unconditionally (non-ASCII in messages/tags degrades to `?`, identical
behavior across pwsh/cmd/bash codepages). Exit codes ARE the verdict — never
re-derive pass/fail by parsing text. Piping into `head` is safe
(`BrokenPipeError` → clean exit 0). Console output goes to a temp file; only
the last 8 lines are ever echoed — never `cat` the temp file, a `.trx`, or a
`.sarif` directly. The extracted table is the only permitted path into
context.

### Quick Reference — by scenario

Match the situation you're actually in, run that command, done. The
per-command sections below explain *why*; this table exists so you don't
have to derive the invocation from the grammar every time. `<target>` = the
.sln/.csproj in play; every command also takes `--root .` unless you're
already inside the repo root.

**Build**

| Scenario | Command |
|---|---|
| Routine build at a gate / "does it compile" | `amtcz sarif build <target> --max 30` |
| Just built, error table got truncated | `amtcz sarif probe --max 60` — **not** another build |
| Need warnings too, not just errors | add `--warnings` to whichever of the two above you're already running |
| Suspect stale/carried logs — branch switch, a project was removed from the solution, or the human explicitly asked for a clean build | `amtcz sarif build <target> --rebuild` |
| Build exit 2 (zero SARIF logs anywhere) | infrastructure problem, not a flag problem — report the console tail; don't retry with different flags |
| Build exit 3 (GAP: build failed but SARIF is clean) | MSBuild-level failure (restore/SDK/references), not a compiler error — report the console-tail line; running `sarif probe` won't find errors that were never written |
| Build exit 4 (dotnet not on PATH) | environment problem — surface to the human, don't retry |

**Test**

| Scenario | Command |
|---|---|
| Tests right after a successful build, same gate | `amtcz test run <target> --no-build --max 25` |
| Running tests without a build earlier this session | `amtcz test run <target> --max 25` (omit `--no-build`) |
| Just ran tests, failure table got truncated | `amtcz test probe --max 60` — **not** another test run |
| Re-verifying one or a few specific tests after a fix | `amtcz test run <target> --no-build --filter "<expr>" --max 25` |
| Test exit 2 (no/malformed TRX) | host crash or logger/results-dir mismatch — report the console tail, don't retry blind |
| Test exit 3 (GAP: TRX present, 0 tests discovered) | bad `--filter` or wrong target — fix the invocation once, don't loop |

**Experience routing**

| Scenario | Command |
|---|---|
| Start of any task (routing step 2) | `amtcz exp inventory` |
| Tags/symptom/keywords derived, need candidates (routing step 4) | `amtcz exp search --tag <tag> --symptom "<fragment>" --keyword "<term>"` |
| `exp inventory` returned exit 2 (no entries yet) | skip search entirely — FRESH problem, per routing step 2 |

### sarif build — compile + SARIF-logged diagnostics

```
amtcz sarif build [target] [--root .] [--pattern GLOB] [--max N] [--warnings] [--rebuild]
```

Runs `dotnet build [target] -v q -nologo -p:ErrorLog="obj/msbuild.sarif%2Cversion=2.1"`,
console redirected to a temp file (last 8 lines echoed, Time Elapsed
included), then extracts a deduped error table. Existing SARIF logs are NOT
deleted before build — MSBuild skips CSC on up-to-date projects, so a
carried log is still valid evidence of an unchanged compile; the report's
`logs: N fresh, M carried` line says which.

| Exit | Meaning |
|---|---|
| 0 | build succeeded, no compiler errors |
| 1 | compiler errors — table printed |
| 2 | zero SARIF logs anywhere, fresh or carried — ErrorLog not applied |
| 3 | GAP — build failed but SARIF shows zero errors (MSBuild-level: restore/SDK/references) |
| 4 | dotnet not on PATH |

`--rebuild` — deletes all logs AND passes `--no-incremental` (full recompile,
all logs fresh). Human-requested only, for branch switches or suspect stale
logs — pays full build cost, never a default. `--pattern` default
`**/obj/**/msbuild.sarif`. `--max` default 30 rows.

### sarif probe — re-extract without building

```
amtcz sarif probe [--root .] [--pattern GLOB] [--max N] [--warnings]
```

Same extraction as `sarif build`, over logs already on disk — use for a
larger `--max` after truncation or `--warnings` on request. Never rebuild
just to re-read. Exit: 0 no errors, 1 errors, 2 no SARIF files found.

### test run — dotnet test via TRX, failure-only

```
amtcz test run [target] [--root .] [--results-dir TestResults/trx] [--no-build] [--filter EXPR] [--max N]
```

Deletes the stale TRX, runs `dotnet test [target] [--no-build]
[--filter EXPR] -v q --nologo --logger "trx;LogFileName=amtcz-results.trx"
--results-directory <dir>`, console redirected (last 8 lines echoed), then
extracts a failure-only table: test, repo-relative file:line (first repo
stack frame, bin/obj skipped), first message clause, plus an exception-type
cluster line. `NotExecuted`/`Inconclusive` never fail the run — they ride in
the summary's "other" count only.

| Exit | Meaning |
|---|---|
| 0 | ran, zero failures |
| 1 | one or more failed/errored tests — table printed |
| 2 | no/malformed TRX (host crash, dropped logger, results-dir mismatch) |
| 3 | GAP — TRX present but 0 tests discovered (bad filter, wrong target, no test SDK) |
| 4 | dotnet not on PATH |

`--no-build` — use right after a successful `sarif build`; binaries already
fresh. `--max` default 25 rows.

### test probe — re-read TRX without rerunning

```
amtcz test probe [--root .] [--results-dir TestResults/trx] [--max N]
```

Same extraction as `test run`, over the TRX already on disk. Never rerun a
suite to re-read results that exist. Exit: 0/1/2/3 as above.

### exp inventory — tag frequency (routing step 2)

```
amtcz exp inventory [--root .]
```

Tag frequency table over `docs/experiences/*.md` frontmatter. Exit: 0 ran
(0 entries is a valid empty table), 2 = `docs/experiences/` has no entries.

### exp search — candidates + Use-When confirmation (routing step 4)

```
amtcz exp search [--root .] [--tag T]... [--symptom S] [--keyword K]... [--max N]
```

`--tag`/`--symptom` match frontmatter only; `--keyword` is a repeatable
full-text fallback. Never prints lesson bodies — routing is decided from the
Use-When column alone (~10 lines/entry). `--max` default 8. Exit: 0 ran (0
hits is valid), 1 no search flags given, 2 no entries yet.
