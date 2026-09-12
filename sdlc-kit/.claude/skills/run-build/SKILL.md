---
name: run-build
description: Compile a .NET solution or project via the `sarif_build` tool and report an error-only structured table (file, line, code, message); raw build logs never enter context. Use at verification gates, in compile-fix loops, or when the human asks to build / "does it compile" / "what's broken". Reports only — never fixes.
---

# Run Build

The `sarif_build` tool owns the whole sequence — `dotnet build -v q -nologo`
with per-project SARIF output, console to a temp file (last 8 lines echoed,
Time Elapsed included), a `logs: N fresh, M carried` line, and the deduped
error table. Carried logs are valid evidence: MSBuild skips the compiler for
up-to-date projects, so a carried log reflects unchanged inputs. The returned
`verdict` field IS the verdict; never re-derive it from the output.

`sarif_build`/`sarif_probe` are assumed registered — there is no fallback
branch and no degraded mode. If the tool is unavailable, stop and tell the
human; never substitute raw `dotnet build` or grep console text on your own
initiative. Scenario table: CLAUDE.md → Reference — amtcz-mcp tools.

## Procedure

1. Target: use the named .sln/.csproj; else Glob `*.sln` at root (single hit
   → use it; multiple → pick by task context and say which).
2. One tool call:
   ```
   sarif_build(target=<target>, root=".", max_rows=30)
   ```
   Verdict contract:
   | verdict | Meaning | Then |
   |---|---|---|
   | `success` | build succeeded, no compiler errors | report SUCCESS + elapsed + warning count |
   | `errors_found` | compiler errors — table printed | report FAILED with the table |
   | `no_sarif_logs` | zero SARIF logs anywhere (none fresh, none carried) | ErrorLog not applied — infrastructure problem; report the console tail line, no retries |
   | `gap_msbuild_failure` | build failed but zero compiler diagnostics — MSBuild-level (restore/SDK/references) | single error row from the informative console-tail line; no param-juggling retries |
   | `dotnet_not_found` | dotnet not on PATH | environment problem; surface to the human |
3. Re-inspection without rebuilding (a larger `max_rows` after truncation, or
   `warnings=true` on request):
   ```
   sarif_probe(root=".", max_rows=60)
   ```
   Never rebuild just to re-read a report that is already on disk.
4. On success report elapsed (from the echoed console tail) plus the warning
   count only — no warning list unless asked (`warnings=true` prints it).

## Report Format

```
Build: <target> — SUCCESS | FAILED (<n> errors) — <elapsed>

<a markdown table built from the tool's errors/warnings list>

First error: <its line — which project it broke; its cascade verdict>
Truncated: <its line>
```

## Rules

- Paths are repo-relative exactly as emitted — they route into engineer
  dispatches.
- >30 distinct errors → truncated to 30 + total + isolate-the-project
  recommendation; use `sarif_probe` with a larger `max_rows` only on explicit
  request.
- `rebuild=true` (deletes all logs + `--no-incremental`, full recompile) only
  after branch switches or when carried logs are suspect (e.g. a project was
  removed from the solution) — and only on explicit human request; it pays
  the full build cost.
- Never `cat` the console temp file or any msbuild.sarif — the echoed tail
  and the table are the only build output permitted into context.
- Report facts only — no fix proposals; fixing is the engineer's job.
