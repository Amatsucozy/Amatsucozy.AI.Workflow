# amtcz CLI — Full Command Reference

Loaded on demand when the `amtcz-cli` skill triggers — not part of
CLAUDE.md's always-on context, and not needed for the single command each
of `run-build`, `run-test`, or CLAUDE.md's experience routing already
inlines. Come here for anything beyond that.

`amtcz --version` — sanity check first. A rejected documented flag below
means the installed CLI predates this doc; upgrade per amtcz-cli/README.md.

---

## sarif build — compile + SARIF-logged diagnostics

```
amtcz sarif build [target] [--root .] [--pattern GLOB] [--max N] [--warnings] [--rebuild]
```

Runs `dotnet build [target] -v q -nologo -p:ErrorLog="obj/msbuild.sarif%2Cversion=2.1"`,
console redirected to a temp file (last 8 lines echoed), then extracts a
deduped error table. Existing SARIF logs are **not** deleted before build —
MSBuild skips CSC on up-to-date projects, so a carried log is still valid
evidence of an unchanged compile; the report's `logs: N fresh, M carried`
line says which.

| Exit | Meaning |
|---|---|
| 0 | build succeeded, no compiler errors |
| 1 | compiler errors — table printed |
| 2 | zero SARIF logs anywhere, fresh or carried — ErrorLog not applied |
| 3 | GAP — build failed but SARIF shows zero errors (MSBuild-level: restore/SDK/references) |
| 4 | dotnet not on PATH |

`--rebuild` — deletes all logs AND passes `--no-incremental` (full recompile,
all logs fresh). Human-requested only, for branch switches or suspect stale
logs — pays full build cost, never a default.

`--pattern` default `**/obj/**/msbuild.sarif`. `--max` default 30 rows.

## sarif probe — re-extract without building

```
amtcz sarif probe [--root .] [--pattern GLOB] [--max N] [--warnings]
```

Same extraction as `sarif build`, over logs already on disk — use for a
larger `--max` after truncation or `--warnings` on request. Never rebuild
just to re-read. Exit: 0 no errors, 1 errors, 2 no SARIF files found.

---

## test run — dotnet test via TRX, failure-only

```
amtcz test run [target] [--root .] [--results-dir TestResults/trx] [--no-build] [--filter EXPR] [--max N]
```

Deletes the stale TRX, runs `dotnet test [target] [--no-build] [--filter EXPR]
-v q --nologo --logger "trx;LogFileName=amtcz-results.trx" --results-directory <dir>`,
console redirected (last 8 lines echoed), then extracts a failure-only
table: test, repo-relative file:line (first repo stack frame, bin/obj
skipped), message, plus an exception-type cluster line. `NotExecuted` /
`Inconclusive` never fail the run — they ride in the summary's "other"
count only.

| Exit | Meaning |
|---|---|
| 0 | ran, zero failures |
| 1 | one or more failed/errored tests — table printed |
| 2 | no/malformed TRX (host crash, dropped logger, results-dir mismatch) |
| 3 | GAP — TRX present but 0 tests discovered (bad filter, wrong target, no test SDK) |
| 4 | dotnet not on PATH |

`--no-build` — use right after a successful `sarif build`; binaries already
fresh. `--max` default 25 rows.

## test probe — re-read TRX without rerunning

```
amtcz test probe [--root .] [--results-dir TestResults/trx] [--max N]
```

Same extraction as `test run`, over the TRX already on disk. Never rerun a
suite to re-read results that exist. Exit: 0/1/2/3 as above.

---

## exp inventory — tag frequency (routing step 2)

```
amtcz exp inventory [--root .]
```

Tag frequency table over `docs/experiences/*.md` frontmatter. Exit: 0 ran
(0 entries is a valid empty table), 2 = `docs/experiences/` has no entries.

## exp search — candidates + Use-When confirmation (routing step 4)

```
amtcz exp search [--root .] [--tag T]... [--symptom S] [--keyword K]... [--max N]
```

`--tag`/`--symptom` match frontmatter only; `--keyword` is a repeatable
full-text fallback. Never prints lesson bodies — routing is decided from
the Use-When column alone (~10 lines/entry). `--max` default 8.

Exit: 0 ran (0 hits is valid), 1 no search flags given, 2 no entries yet.

---

## Shared behavior

- All output is pure ASCII, unconditionally — non-ASCII in messages/tags
  degrades to `?`; identical behavior across pwsh/cmd/bash codepages.
- Exit codes ARE the verdict — never re-derive pass/fail by parsing text.
- Piping into `head` is safe (`BrokenPipeError` → clean exit 0).
- Console output goes to a temp file; only the last 8 lines are ever
  echoed. Never `cat` the temp file, a `.trx`, or a `.sarif` directly.
