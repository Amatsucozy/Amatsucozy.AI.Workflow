# Research Brief — adhoc-amtcz-mcp

## Summary

`amtcz-cli/amtcz.py` (single-module, stdlib-only, argparse-based) implements
six operations across three domains: SARIF build diagnostics, TRX test
results, and experience-memory routing. Each operation's exit code IS its
verdict (0-4 depending on command) and its human-facing output is a printed
ASCII markdown table. No MCP server code, Dockerfile, or test suite exists
anywhere in the repo yet — this is a from-scratch build. Three sdlc-kit
documents consume the CLI by shelling out and documenting its flags/exit
codes in prose: `sdlc-kit/CLAUDE.md`, `sdlc-kit/.claude/skills/run-build/SKILL.md`,
`sdlc-kit/.claude/skills/run-test/SKILL.md`.

## Per-Operation Inventory (amtcz-cli/amtcz.py)

### sarif_build
- Entry: `cmd_sarif_build()` L202-268, calls `run_probe()` L128-181.
- Flags: `target` (positional, optional), `--rebuild`, `--root` (default `.`),
  `--pattern` (default `**/obj/**/msbuild.sarif`), `--max` (default 30),
  `--warnings`.
- Exit codes: 0 build ok/no errors; 1 compiler errors; 2 zero SARIF logs
  anywhere; 3 GAP (build failed, SARIF clean — MSBuild-level); 4 dotnet not
  on PATH.
- Data: error/warning rows `{level,code,file,line,msg}` (from
  `load_diagnostics()` L97-115, sourced via `find_sarif_files()` L118-125),
  first-error detail, cascade verdict (`CASCADE_CODES` L74-75), logs
  fresh/carried counts, console tail (last 8 lines), truncation state.

### sarif_probe
- Entry: `cmd_sarif_probe()` L184-185 -> `run_probe()` L128-181.
- Flags: `--root`, `--pattern`, `--max`, `--warnings` (no target).
- Exit codes: 0 no errors; 1 errors; 2 no SARIF files found.
- Data: same shape as sarif_build minus build/console fields.

### test_run
- Entry: `cmd_test_run()` L433-472, calls `trx_report()` L375-430.
- Flags: `target` (optional), `--root`, `--results-dir` (default
  `TestResults/trx`), `--no-build`, `--filter`, `--max` (default 25).
- Exit codes: 0 zero failures; 1 failures found; 2 no/malformed TRX; 3 GAP
  (TRX present, 0 tests discovered); 4 dotnet not on PATH.
- Data: failure rows `{name,class,outcome,message,location}` (from
  `parse_trx_failures()` L324-355, `_first_repo_frame()` L284-311), summary
  counters (total/passed/failed/other, `read_trx_summary()` L358-372),
  cluster verdict (`_exception_type()` L314-321), console tail, truncation.

### test_probe
- Entry: `cmd_test_probe()` L475-478 -> `trx_report()` L375-430.
- Flags: `--root`, `--results-dir`, `--max` (no target, no `--no-build`, no
  `--filter`).
- Exit codes: 0/1/2/3 (no 4 — no dotnet invocation).
- Data: same shape as test_run minus console/exec fields.

### exp_inventory
- Entry: `cmd_exp_inventory()` L565-583, via `load_entries()` L534-553 /
  `parse_frontmatter()` L505-531.
- Flags: `--root`.
- Exit codes: 0 ran (0 entries is a valid empty table); 2 no entries yet.
- Data: tag -> count table, malformed-entry paths.

### exp_search
- Entry: `cmd_exp_search()` L586-644, via `load_entries()`.
- Flags: `--root`, `--tag` (repeatable), `--symptom`, `--keyword`
  (repeatable), `--max` (default 8).
- Exit codes: 0 ran (0 hits valid); 1 no search flags given; 2 no entries
  yet.
- Data: scored hits `{slug, matched_on, use-when, path}` (`AXIS_WEIGHT`
  L485), total vs shown count, malformed-entry paths.

## Reuse Classification

**Pure data extraction — logic can be lifted near-verbatim into amtcz-mcp
(vendored independently, per the "no dependency on amtcz-cli" decision):**
`load_diagnostics`, `find_sarif_files`, `parse_trx_failures`,
`read_trx_summary`, `load_entries`, `parse_frontmatter`, `_first_repo_frame`,
`_exception_type`, `uri_to_rel`, `strip_comment`.

**Mixed print+logic — the CLI conflates "compute the verdict/data" with
"format an ASCII table"; amtcz-mcp needs the compute half only, returning
structured data instead of printing:** `run_probe`, `trx_report`,
`cmd_sarif_build`, `cmd_test_run`, `cmd_exp_inventory`, `cmd_exp_search`.
None of these can be imported as-is even if amtcz-mcp depended on amtcz-cli
(it won't, per decision) — every one needs its printing stripped and its
return value promoted from an exit-code int to a structured result.

## Doc Consumer Locations

### sdlc-kit/CLAUDE.md
- L18: routing step 2 runs `amtcz exp inventory`.
- L33: routing step 4 runs `amtcz exp search --tag <tag> --symptom "<fragment>" --keyword "<term>"`.
- L58: subagent note — "`amtcz` is on the machine PATH, so it resolves for
  subagent Bash calls too".
- L65-81: Reference section header — guarantees on PATH, no fallback, ASCII
  output, exit-codes-are-verdict, console-tail-only rule.
- L83-120: Quick Reference scenario tables (Build/Test/Experience) — full
  command templates.
- L122-146: `sarif build` full reference (signature, behavior, exit table,
  flags).
- L148-156: `sarif probe` full reference.
- L158-181: `test run` full reference (signature, behavior, exit table,
  flags).
- L183-190: `test probe` full reference.
- L192-199: `exp inventory` full reference.
- L201-210: `exp search` full reference.

### sdlc-kit/.claude/skills/run-build/SKILL.md
- L3: frontmatter description names `amtcz sarif build`.
- L16: "`amtcz` is guaranteed installed and is the only path — no fallback
  branch."
- L19: pointer to CLAUDE.md Reference section for full flags.
- L28: the command itself — `amtcz sarif build <target> --root . --max 30`.
- L30-37: exit code contract table (0-4).
- L41: re-inspection command — `amtcz sarif probe --root . --max 60`.
- L53: Report Format expects "<the amtcz table verbatim>".

### sdlc-kit/.claude/skills/run-test/SKILL.md
- L3: frontmatter description names `amtcz test run`.
- L14: same "guaranteed installed, only path" guarantee.
- L18: pointer to CLAUDE.md Reference section.
- L27: the command — `amtcz test run <target> --root . --no-build [--filter "<expr>"] --max 25`.
- L29-36: exit code contract table (0-4).
- L39: re-inspection command — `amtcz test probe --root . --max 60`.
- L48: Report Format expects "<the amtcz table verbatim (Test | Location | Failure)>".

### Other repo references (context only, not in AC scope per ticket)
- `README.md` L32-34: notes the CLI reference lives in CLAUDE.md.
- `amtcz-cli/README.md` L116-130: "Consumers" section listing the same three
  documents — worth a deprecation note per AC-5, but content otherwise
  untouched.
- `sdlc-kit/TUNING.md` L24/64/67, `sdlc-kit/MIGRATION.md` L18,
  `sdlc-kit/SESSION.md` L9: incidental mentions, explicitly out of scope
  per ticket's Non-goal.

## Test & Prior-Art Status
- No test files (`test_*.py`, `conftest.py`, `tests/`) exist anywhere in the
  repo — amtcz-mcp's pytest suite (AC-6) is a from-scratch addition.
- No MCP server code, `mcp`-dependent `requirements.txt`/`pyproject.toml`, or
  Dockerfile exists anywhere in the repo — amtcz-mcp is a from-scratch
  package, no template to extend.
