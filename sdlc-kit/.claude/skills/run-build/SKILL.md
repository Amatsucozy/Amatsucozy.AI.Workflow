---
name: run-build
description: Compile a .NET solution/project and produce an error-only structured report (file, line, code, message) without raw build logs entering context. Use whenever a build must run — at verification gates, in compile-check fix loops, or when the human asks "build", "does it compile", "what's broken". Never at normal verbosity; never for fixing.
---

# Run Build

Compile and report failures with surgical precision. Raw logs never enter
context — only the capped pipeline output below, restructured into the table.

## Procedure

1. Target: use the named .sln/.csproj; else Glob `*.sln` at root (single hit →
   use it; multiple → pick by task context and say which).
2. Always build quiet and capped:
   `dotnet build <target> -v q -nologo -clp:ErrorsOnly;NoSummary 2>&1 | grep -E "error|Error" | head -60`
3. Parse `path(line,col): error CODE: message [project.csproj]`. Dedupe
   multi-target duplicates. Order by build sequence — the FIRST error matters;
   later ones are often cascade.
4. On success report elapsed + warning count only (no warning list unless asked).

## Report Format

```
Build: <target> — SUCCESS | FAILED (<n> errors) — <elapsed>

| # | File | Line | Code | Message |
|---|------|------|------|---------|

First error: <verbatim, which project it broke, whether the rest look like
cascade (downstream missing-type/namespace errors usually are)>
Truncated: none | first N of M — rebuild <project> in isolation for the rest
```

## Rules

- Paths repo-relative exactly as the compiler printed — they route into
  engineer dispatches.
- >30 distinct errors → first 30 + total + isolate-the-project recommendation.
- Pre-compilation failures (restore, SDK, bad reference) → single error row
  with the informative output line; no flag-juggling retries.
- Report facts only — no fix proposals; fixing is the engineer's job.
