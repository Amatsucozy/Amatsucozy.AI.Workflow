---
name: run-test
description: Run a .NET test suite or filtered scope and produce a failure-only structured report (test, file:line, message) without raw test output entering context. Use whenever tests must run — at verification gates (with --no-build after a successful build), in failing-test fix loops, or when the human asks to "run tests", "why are tests failing". Never for fixing; never for verdicts beyond pass/fail counts.
---

# Run Test

Run tests and report failures with surgical precision. Raw output never enters
context — only the capped pipeline below, restructured into the table.

## Procedure

1. Run exactly the scope given (project, `--filter`, or full suite) — never
   widen or narrow it.
2. Default `--no-build` when binaries are fresh (always true right after a
   successful build step). Quiet and capped:
   `dotnet test <target> --no-build -v q --logger "console;verbosity=minimal" 2>&1 | grep -E "Failed|Passed!|error" | head -80`
3. For each failure, extract: test name; location = first stack frame inside
   the repo (skip framework frames); message = assertion/exception first line,
   one clause. Never include stacks.

## Report Format

```
Tests: <scope> — PASS | FAIL — <passed>/<total>, <failed> failed, <skipped> skipped — <elapsed>

| # | Test | Location | Failure |
|---|------|----------|---------|

Clusters: <"failures 2–6 all NullReference in Fixture.Setup" style one-liner, or none>
Truncated: none | first N of M — re-run with --filter for the rest
```

## Rules

- Locations repo-relative — they route into engineer dispatches.
- >25 distinct failures → first 25 + total + filtered-rerun recommendation.
- Infrastructure failures (no tests discovered, stale binaries, bad filter) →
  single error row with the informative line; retry only if asked.
- Facts only — no fixes, no acceptability judgments beyond the counts.
