---
name: run-test
description: Run a .NET test suite or filtered scope and produce a failure-only structured report (test, file:line, message) via `amtcz test run` — one command runs the stale-TRX cleanup, the quiet TRX-logged test run, and the extraction; raw test output never enters context. Use whenever tests must run — at verification gates (with --no-build after a successful build), in failing-test fix loops, or when the human asks to "run tests", "why are tests failing". Never for fixing; never for verdicts beyond pass/fail counts.
---

# Run Test

Run tests and report failures with surgical precision. `amtcz test run` owns
the whole sequence — stale-TRX cleanup, `dotnet test -v q --nologo` with the
TRX logger, console to a temp file (last 8 lines echoed), and the
failure-only table with repo-relative locations. Its exit code IS the
verdict; never re-derive it from the output.

`amtcz` is guaranteed installed and is the only path — no fallback branch.
If a Bash call reports it missing, stop and tell the human directly; this
skill has no degraded mode. Never grep test console output on your own
initiative. Full flag reference beyond what's below: the `amtcz-cli` skill.

## Procedure

1. Run exactly the scope given (project, `--filter`, or full suite) — never
   widen or narrow it.
2. One command; default `--no-build` when binaries are fresh (always true
   right after a successful `amtcz sarif build`):
   ```bash
   amtcz test run <target> --root . --no-build [--filter "<expr>"] --max 25
   ```
   Exit code contract:
   | Exit | Meaning | Then |
   |---|---|---|
   | 0 | ran, zero failures (skips/inconclusive don't fail) | report PASS + counts |
   | 1 | one or more failed/errored — table printed | report FAIL with the table |
   | 2 | no/malformed TRX (host crash, dropped logger, results-dir mismatch) | infrastructure problem; report the console tail line, no retries |
   | 3 | GAP: TRX present but 0 tests discovered (bad filter, wrong target, no test SDK) | single error row from the console tail; fix the invocation, don't loop |
   | 4 | dotnet not on PATH | environment problem; surface to the human |
3. Re-inspection without rerunning (larger `--max` after truncation):
   ```bash
   amtcz test probe --root . --max 60
   ```
   Never rerun a suite just to re-read results already on disk.

## Report Format

```
Tests: <scope> — PASS | FAIL — <passed>/<total>, <failed> failed, <other> skipped/inconclusive

<the amtcz table verbatim (Test | Location | Failure)>

Clusters: <its line>
Truncated: <its line>
```

## Rules

- Locations are repo-relative exactly as emitted (first repo stack frame,
  bin/obj frames skipped) — they route into engineer dispatches.
  `[no repo frame]` rows are still real failures; the message is the lead.
- >25 distinct failures → truncated to 25 + total; use `test probe` with a
  larger `--max`, or a narrower `--filter` rerun, only on explicit request.
- Never `cat` the console temp file or any .trx — the echoed tail and the
  table are the only test output permitted into context.
- Facts only — no fixes, no acceptability judgments beyond the counts.
- Add `TestResults/` to the repo .gitignore if not already there — the TRX
  results dir lives under the repo root.
