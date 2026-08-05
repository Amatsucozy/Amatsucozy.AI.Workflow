---
name: run-build
description: Compile a .NET solution/project and produce an error-only structured report (file, line, code, message) via `amtcz sarif build` — one command runs the clean, the quiet SARIF-logged build, and the extraction; raw build logs never enter context. Use whenever a build must run — at verification gates, in compile-check fix loops, or when the human asks "build", "does it compile", "what's broken". Never at normal verbosity; never for fixing.
---

# Run Build

Compile and report failures with surgical precision. `amtcz sarif build`
owns the whole sequence — `dotnet build -v q -nologo` with per-project SARIF
output, console to a temp file (last 8 lines echoed, Time Elapsed included),
a `logs: N fresh, M carried` line, and the deduped error table. Carried logs
are valid evidence: MSBuild skips the compiler for up-to-date projects, and
a log whose compile was skipped reflects unchanged inputs. Its exit code IS the
verdict; never re-derive it from the output.

`amtcz` is the only path (CLAUDE.md → Tooling Resolution). If it is not on
PATH, the resolution gate fires BEFORE this skill runs: stop, notify, wait
for the human to install or approve degraded mode. Never grep console text
on your own initiative.

## Procedure

1. Target: use the named .sln/.csproj; else Glob `*.sln` at root (single hit
   → use it; multiple → pick by task context and say which).
2. One command:
   ```bash
   amtcz sarif build <target> --root . --max 30
   ```
   Exit code contract:
   | Exit | Meaning | Then |
   |---|---|---|
   | 0 | build succeeded, no compiler errors | report SUCCESS + elapsed + warning count |
   | 1 | compiler errors — table printed | report FAILED with the table |
   | 2 | zero SARIF logs anywhere (none fresh, none carried) | ErrorLog not applied — infrastructure problem; report the console tail line, no retries |
   | 3 | GAP: build failed but zero compiler diagnostics — MSBuild-level (restore/SDK/references) | single error row from the informative console-tail line; no flag-juggling retries |
   | 4 | dotnet not on PATH | environment problem; surface to the human |
3. Re-inspection without rebuilding (e.g. a larger `--max` after
   truncation, or `--warnings` on request):
   ```bash
   amtcz sarif probe --root . --max 60
   ```
   Never rebuild just to re-read a report that is already on disk.
4. On success report elapsed (Time Elapsed line is in the echoed console
   tail) plus the warning count only — no warning list unless asked
   (`--warnings` prints it when it is).

## Report Format

```
Build: <target> — SUCCESS | FAILED (<n> errors) — <elapsed>

<the amtcz table verbatim>

First error: <its line — which project it broke; its cascade verdict>
Truncated: <its line>
```

## Rules

- Paths are repo-relative exactly as emitted — they route into engineer
  dispatches.
- >30 distinct errors → truncated to 30 + total + isolate-the-project
  recommendation; use `sarif probe` with a larger `--max` only on explicit
  request.
- `--rebuild` (deletes all logs + `--no-incremental`, full recompile) only
  after branch switches or when carried logs are suspect (e.g. a project was
  removed from the solution) — and only on explicit human request; it pays
  the full build cost.
- Never `cat` the console temp file or any msbuild.sarif — the echoed tail
  and the table are the only build output permitted into context.
- Report facts only — no fix proposals; fixing is the engineer's job.

*Degraded mode (session-approved only, per CLAUDE.md):* the verbatim
build+grep commands from CLAUDE.md's degraded table replace step 2; the
report carries a `tooling: degraded` line, no dedupe, no cascade verdict,
and the gap rule falls back to manually comparing build-exit against the
grep hits.