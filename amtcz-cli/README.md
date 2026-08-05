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

## Usage

```
amtcz sarif build [target] [--root .] [--pattern G] [--max 30] [--warnings]
    The run-build sequence in one command: delete stale obj/msbuild.sarif
    logs (cross-platform walk, skips bin/), run
      dotnet build [target] -v q -nologo -p:ErrorLog="obj/msbuild.sarif%2Cversion=2.1"
    with console redirected to <tmp>/amtcz-build-console.txt (last 8 lines
    echoed, Time Elapsed included), then extract the deduped error table.
    Exit — the verdict, no output-parsing needed:
      0 = build succeeded, no compiler errors
      1 = compiler errors (table printed, cascade verdict included)
      2 = no SARIF logs produced (ErrorLog flags not applied)
      3 = GAP: build failed but SARIF shows zero compiler diagnostics —
          MSBuild-level failure (restore/SDK/project references); the
          informative line is in the echoed console tail
      4 = dotnet not found on PATH

amtcz sarif probe [--root .] [--pattern G] [--max 30] [--warnings]
    Extraction only, over SARIF logs already on disk — re-read a truncated
    report with a larger --max, or add --warnings, without rebuilding.
    Exit: 0 = no errors, 1 = errors, 2 = no SARIF files found.

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
0/1/2/3/4 directly, and the experience routing branches FRESH/HISTORICAL
off `exp`'s. Piping into `head` is safe (BrokenPipeError → clean exit 0).

## Consumers

- `CLAUDE.md` → Tooling Resolution (session probe, STOP gate, degraded-mode
  table) and Experience-First Task Routing steps 1/3.
- `.claude/skills/run-build/SKILL.md` (single `sarif build` call; gap rule
  keys off exit 3).

This CLI is the single source of truth; the per-skill scripts it replaced
(`sarif_report.py`, `experience_lookup.py`) are deleted from the kit.

## Changelog

- 0.2.0 — `sarif` split into `build` (owns clean + dotnet build + extract;
  exit 3 = MSBuild-level gap, exit 4 = no dotnet) and `probe` (extract
  only). All output forced to pure ASCII for terminal safety.
- 0.1.0 — merged `sarif_report.py` + `experience_lookup.py`.