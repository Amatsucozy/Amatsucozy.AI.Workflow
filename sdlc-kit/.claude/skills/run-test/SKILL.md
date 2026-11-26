---
name: run-test
description: Run a .NET test suite or filtered scope via the `test_run` tool and report a failure-only structured table (test, file:line, message); raw test output never enters context. Use at verification gates (no_build=true after a successful build), in failing-test fix loops, or when the human asks to run tests / "why are tests failing". Reports pass/fail counts only — never fixes.
---

# Run Test

`test_run` runs the tests with TRX logging and returns a failure-only table
with repo-relative locations and a `verdict`; the tool's own description
explains each verdict. Use the verdict as given. If the tool is unavailable,
stop and tell the human — never substitute raw `dotnet test`.

## Procedure

1. Run exactly the scope given (project, `filter`, or full suite).
2. `test_run(target=<target>, root=<project root>, no_build=true, filter="<expr>", max_rows=25)`
   — `no_build=true` when binaries are fresh (always right after a successful
   `sarif_build`); omit it otherwise.
3. To see more rows, re-read with `test_probe(root=<same root>, max_rows=60)`
   instead of rerunning.

## Report

```
Tests: <scope> — PASS | FAIL — <passed>/<total>, <failed> failed, <other> skipped/inconclusive

<markdown table from the tool's failures (Test | Location | Failure)>

Clusters: <its line>
Truncated: <its line>
```

- Over 25 distinct failures: show 25 and the total; widen with `test_probe` or
  a narrower `filter` only on request.
- Keep locations repo-relative exactly as emitted. `[no repo frame]` rows are
  still real failures; the message is the lead.
- For infrastructure verdicts, report the console-tail line and stop;
  `zero_discovered` gets one corrected invocation.
- If `TestResults/` is missing from the repo's .gitignore, say so — adding it
  is for the engineer or the human.
- Facts only — no fixes or acceptability judgments beyond the counts.
