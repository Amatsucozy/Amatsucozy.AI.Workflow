---
name: run-build
description: Compile a .NET solution or project via the `sarif_build` tool and report an error-only structured table (file, line, code, message); raw build logs never enter context. Use at verification gates, in compile-fix loops, or when the human asks to build / "does it compile" / "what's broken". Reports only — never fixes.
---

# Run Build

`sarif_build` runs the build, collects per-project SARIF, and returns a
deduped error table with a `verdict`; the tool's own description explains each
verdict. Use the verdict as given. If the tool is unavailable, stop and tell
the human — never substitute raw `dotnet build`.

## Procedure

1. Target: the named .sln/.csproj; otherwise Glob `*.sln` at the root (one
   hit → use it; several → pick by task context and say which).
2. `sarif_build(target=<target>, root=<project root>, max_rows=30)`.
3. To see more rows or warnings, re-read with
   `sarif_probe(root=<same root>, max_rows=60)` instead of rebuilding.
4. `rebuild=true` only on explicit human request (branch switch, removed
   project, suspected stale logs). Carried logs from up-to-date projects are
   valid evidence.

## Report

```
Build: <target> — SUCCESS | FAILED (<n> errors) — <elapsed>

<markdown table from the tool's errors (or warnings, when asked)>

First error: <its line — which project it broke; its cascade verdict>
Truncated: <its line>
```

- On success, give elapsed time and the warning count only.
- Over 30 distinct errors: show 30, the total, and recommend isolating the
  project; use `sarif_probe` with a larger `max_rows` only on request.
- Keep paths repo-relative exactly as emitted — they route into engineer
  dispatches.
- For infrastructure verdicts, report the console-tail line and stop.
- Facts only — fixing is the engineer's job.
