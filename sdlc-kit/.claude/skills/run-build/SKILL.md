---
name: run-build
description: Compile a .NET solution/project with per-project SARIF error logging and produce an error-only structured report (file, line, code, message) via the sarif_report.py extraction script — raw build logs never enter context. Use whenever a build must run — at verification gates, in compile-check fix loops, or when the human asks "build", "does it compile", "what's broken". Never at normal verbosity; never for fixing.
---

# Run Build

Compile and report failures with surgical precision. Diagnostics come from
structured SARIF (`-p:ErrorLog`), not from grepping console text — exact
file/line/code/message, no regex fragility, multi-target duplicates deduped by
the script. Console output goes to a temp file; only a short tail enters
context, and only for MSBuild-level failures SARIF cannot see.

## Procedure

1. Target: use the named .sln/.csproj; else Glob `*.sln` at root (single hit →
   use it; multiple → pick by task context and say which).
2. Clean stale logs, build quiet with SARIF output, console to temp file —
   one batched Bash call:
   ```bash
   find . -path '*/obj/msbuild.sarif' -delete 2>/dev/null; \
   dotnet build <target> -v q -nologo \
     -p:ErrorLog="obj/msbuild.sarif%2Cversion=2.1" \
     > /tmp/build-console.txt 2>&1; \
   echo "build-exit:$?"; tail -8 /tmp/build-console.txt
   ```
   (Relative ErrorLog path resolves per project → each writes its own
   `obj/msbuild.sarif`; obj/ is already gitignored. The `%2C` is the escaped
   comma so MSBuild doesn't split the property value.)
3. Extract — same Bash turn or the next:
   ```bash
   python3 ~/.claude/skills/run-build/scripts/sarif_report.py --root . --max 30
   ```
   The script (stdlib only) merges every `obj/msbuild.sarif`, dedupes,
   orders by compile sequence (log mtime) then line, prints the error table,
   the verbatim first error, and a cascade assessment. Exit: 0 clean,
   1 errors, 2 no logs found.
4. **Gap rule.** `build-exit` ≠ 0 but the script reports zero errors (or
   exit 2) → the failure is MSBuild-level (restore, SDK, bad project
   reference) — ErrorLog captures compiler diagnostics only. Report a single
   error row from the informative line in the console tail; no flag-juggling
   retries.
5. On success report elapsed (from the console tail's Time Elapsed line) plus
   the script's warning count only — no warning list unless asked
   (`--warnings` prints it when it is).

## Report Format

```
Build: <target> — SUCCESS | FAILED (<n> errors) — <elapsed>

<the script's table verbatim>

First error: <script's line — which project it broke; script's cascade verdict>
Truncated: <script's line>
```

## Rules

- Paths are repo-relative exactly as the script emits them — they route into
  engineer dispatches.
- >30 distinct errors → the script truncates to 30 + total + isolate-the-
  project recommendation; pass a larger `--max` only on explicit request.
- Never `cat` /tmp/build-console.txt or any msbuild.sarif — the tail and the
  script's table are the only build output permitted into context.
- Report facts only — no fix proposals; fixing is the engineer's job.