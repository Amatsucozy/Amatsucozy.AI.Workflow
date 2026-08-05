# amtcz

Standalone CLI for the AMaTsuCoZy SDLC kit — SARIF-logged .NET builds,
build-report extraction, and experience-memory lookup. Stdlib-only runtime;
setuptools at build time only.

**All output is pure ASCII, unconditionally.** Legacy console codepages
(cp1252/cp437 under some pwsh/cmd setups) garble or truncate non-ASCII
stdout; every emitted line is sanitized, and non-ASCII characters inside
data (compiler messages, tags) degrade to `?`. Behavior is identical on
every shell.

## Install

```bash
pipx install <path-or-git-url>          # preferred: isolated, on PATH
pip install --user <path-or-git-url>    # alternative
py -m pip install --user <path-or-git-url>   # Windows launcher
```

pip generates a native `amtcz` / `amtcz.exe` entry point — identical
behavior in Claude Code sessions, subagents, CI, and manual shells on
macOS, Windows, and Linux. Verify: `amtcz --version`.

Upgrade: `pipx upgrade amtcz` / re-run pip install with `--force-reinstall`.
The kit's session probe echoes the version; a rejected documented flag means
the installed CLI is older than the kit docs — upgrade rather than work
around.

### `amtcz` not recognized after `pip install --user`

pip's `--user` scripts directory is not on PATH by default (pip prints a
warning saying so). Locate it and add it once:

- **pwsh/Windows:** `python -m site --user-base` → shim is under
  `...\Python3XX\Scripts\amtcz.exe`. Persist:
  `[Environment]::SetEnvironmentVariable("Path", $env:Path + ";<that Scripts dir>", "User")`,
  then open a new terminal.
- **bash/zsh:** `python3 -m site --user-base` → shim under `<that>/bin`
  (typically `~/.local/bin`). Add
  `export PATH="$HOME/.local/bin:$PATH"` to your shell rc.

Rule-outs if PATH doesn't fix it: multiple Pythons — compare
`Get-Command python` / `which python3` against the interpreter whose pip
you ran, and reinstall with the explicit one (`py -m pip install --user`).
`python -m amtcz --version` verifies the install independent of PATH.
pipx avoids this entire class of problem (`pipx ensurepath`).

## Usage

```
amtcz sarif build [target] [--rebuild] [--root .] [--pattern G] [--max 30] [--warnings]
    The run-build sequence in one command: run
      dotnet build [target] -v q -nologo -p:ErrorLog="obj/msbuild.sarif%2Cversion=2.1"
    with console redirected to <tmp>/amtcz-build-console.txt (last 8 lines
    echoed, Time Elapsed included), report `logs: N fresh, M carried`, then
    extract the deduped error table. Existing logs are NOT deleted: MSBuild
    skips the compiler for up-to-date projects and the compiler is what
    writes SARIF, so a carried log is valid evidence of an unchanged
    compile. --rebuild deletes all logs AND passes --no-incremental (full
    recompile, all logs fresh) — for branch switches / suspect stale logs.
    Exit — the verdict, no output-parsing needed:
      0 = build succeeded, no compiler errors
      1 = compiler errors (table printed, cascade verdict included)
      2 = zero SARIF logs anywhere, fresh or carried (ErrorLog not applied)
      3 = GAP: build failed but SARIF shows zero compiler diagnostics —
          MSBuild-level failure (restore/SDK/project references); the
          informative line is in the echoed console tail
      4 = dotnet not found on PATH

amtcz sarif probe [--root .] [--pattern G] [--max 30] [--warnings]
    Extraction only, over SARIF logs already on disk — re-read a truncated
    report with a larger --max, or add --warnings, without rebuilding.
    Exit: 0 = no errors, 1 = errors, 2 = no SARIF files found.

amtcz test run [target] [--root .] [--results-dir TestResults/trx]
               [--no-build] [--filter EXPR] [--max 25]
    The run-test sequence in one command: delete the stale TRX, run
      dotnet test [target] [--no-build] [--filter EXPR] -v q --nologo
        --logger "trx;LogFileName=amtcz-results.trx" --results-directory <dir>
    with console redirected to <tmp>/amtcz-test-console.txt (last 8 lines
    echoed), then extract the failure-only table: test, repo-relative
    file:line (first repo stack frame, bin/obj skipped), first message
    clause, plus exception-type cluster analysis. Skipped/inconclusive
    tests count in the summary only — they never fail the run.
    Exit — the verdict, no output-parsing needed:
      0 = ran, zero failures
      1 = one or more failed/errored tests (table printed)
      2 = no/malformed TRX (test host crash, dropped logger arg,
          --results-directory mismatch)
      3 = GAP: TRX present but zero tests discovered (bad filter, wrong
          target, no test SDK reference)
      4 = dotnet not found on PATH

amtcz test probe [--root .] [--results-dir TestResults/trx] [--max 25]
    Extraction only, over the TRX already on disk — re-read a truncated
    report with a larger --max without rerunning the suite.
    Exit: 0/1/2/3 as above.

amtcz exp inventory [--root .]
    Tag frequency table over docs/experiences/*.md frontmatter
    (CLAUDE.md experience routing, step 1).

amtcz exp search [--root .] [--tag T]... [--symptom S] [--keyword K]... [--max 8]
    Candidate entries + Use-When confirmation column (step 3). --tag and
    --symptom match frontmatter only; --keyword scans full text. Never
    prints lesson bodies — routing is decided from ~10 lines/entry.
    Exit: 0 = ran (0 hits valid), 1 = no search flags given,
    2 = docs/experiences/ has no entries yet.
```

Exit codes are contract: the run-build skill routes on `sarif build`'s
0/1/2/3/4 directly, the run-test skill on `test run`'s, and the experience
routing branches FRESH/HISTORICAL off `exp`'s. Piping into `head` is safe (BrokenPipeError → clean exit 0).

## Consumers

- `CLAUDE.md` → Tooling Resolution (session probe, STOP gate, degraded-mode
  table) and Experience-First Task Routing steps 1/3.
- `.claude/skills/run-build/SKILL.md` (single `sarif build` call; gap rule
  keys off exit 3).
- `.claude/skills/run-test/SKILL.md` (single `test run` call; discovery gap
  keys off exit 3).

This CLI is the single source of truth; the per-skill scripts it replaced
(`sarif_report.py`, `experience_lookup.py`) are deleted from the kit.

## Changelog

- 0.3.1 — FIX: `sarif build` no longer deletes logs pre-build. The old
  clean-then-build sequence returned a false "no SARIF logs found" whenever
  MSBuild's incremental check skipped compilation (up-to-date tree =>
  compiler never runs => no log written => the just-deleted logs were the
  only evidence). Now: snapshot mtimes, report fresh vs carried, and treat
  carried logs as valid. `--rebuild` restores clean semantics correctly by
  also forcing `--no-incremental`.

- 0.3.0 — `test run` / `test probe`: dotnet test via TRX with failure-only
  extraction (repo-frame locations, exception-type clusters). Skipped and
  inconclusive tests no longer affect the verdict.

- 0.2.0 — `sarif` split into `build` (owns clean + dotnet build + extract;
  exit 3 = MSBuild-level gap, exit 4 = no dotnet) and `probe` (extract
  only). All output forced to pure ASCII for terminal safety.
- 0.1.0 — merged `sarif_report.py` + `experience_lookup.py`.