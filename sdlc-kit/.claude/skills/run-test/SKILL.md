---
name: run-test
description: Run a .NET test suite or filtered scope and produce a failure-only structured report (test, file:line, message) via the `test_run` tool — one call runs the stale-TRX cleanup, the quiet TRX-logged test run, and the extraction; raw test output never enters context. Use whenever tests must run — at verification gates (with no_build=true after a successful build), in failing-test fix loops, or when the human asks to "run tests", "why are tests failing". Never for fixing; never for verdicts beyond pass/fail counts.
---

# Run Test

Run tests and report failures with surgical precision. The `test_run` tool
owns the whole sequence — stale-TRX cleanup, `dotnet test -v q --nologo` with
the TRX logger, console to a temp file (last 8 lines echoed), and the
failure-only table with repo-relative locations. Its returned `verdict`
field IS the verdict; never re-derive it from the output.

The `test_run`/`test_probe` tools are assumed available — no fallback
branch. If the tool is unavailable/unregistered, stop and tell the human
directly; this skill has no degraded mode. Never grep test console output
on your own initiative. Full reference beyond what's below: CLAUDE.md →
Reference — amtcz-mcp tools (inlined always-on).

## Procedure

1. Run exactly the scope given (project, `filter`, or full suite) — never
   widen or narrow it.
2. One tool call; default `no_build=true` when binaries are fresh (always
   true right after a successful `sarif_build`):
   ```
   test_run(target=<target>, root=".", no_build=true, filter="<expr>", max_rows=25)
   ```
   Verdict contract:
   | verdict | Meaning | Then |
   |---|---|---|
   | `pass` | ran, zero failures (skips/inconclusive don't fail) | report PASS + counts |
   | `fail` | one or more failed/errored — table printed | report FAIL with the table |
   | `no_trx` | no/malformed TRX (host crash, dropped logger, results-dir mismatch) | infrastructure problem; report the console tail line, no retries |
   | `zero_discovered` | TRX present but 0 tests discovered (bad filter, wrong target, no test SDK) | single error row from the console tail; fix the invocation, don't loop |
   | `dotnet_not_found` | dotnet not on PATH | environment problem; surface to the human |
3. Re-inspection without rerunning (larger `max_rows` after truncation):
   ```
   test_probe(root=".", max_rows=60)
   ```
   Never rerun a suite just to re-read results already on disk.

## Report Format

```
Tests: <scope> — PASS | FAIL — <passed>/<total>, <failed> failed, <other> skipped/inconclusive

<a markdown table built from the tool's failures list (Test | Location | Failure)>

Clusters: <its line>
Truncated: <its line>
```

## Rules

- Locations are repo-relative exactly as emitted (first repo stack frame,
  bin/obj frames skipped) — they route into engineer dispatches.
  `[no repo frame]` rows are still real failures; the message is the lead.
- >25 distinct failures → truncated to 25 + total; use `test_probe` with a
  larger `max_rows`, or a narrower `filter` rerun, only on explicit request.
- Never `cat` the console temp file or any .trx — the echoed tail and the
  table are the only test output permitted into context.
- Facts only — no fixes, no acceptability judgments beyond the counts.
- Add `TestResults/` to the repo .gitignore if not already there — the TRX
  results dir lives under the repo root.
