---
slug: relpath-root-must-be-canonicalised-like-its-paths
use-when: "use when a tool reports paths relative to a root taken from an env var or cwd, and the paths it relativises were resolved with realpath/Path.resolve — especially on Windows where Temp and user dirs arrive as 8.3 short names"
domain: python
tags: [python, windows, paths, relpath, mcp, testing]
symptom: "relative path comes back as ../../../../../../Users/<name>/... instead of repo-b/B.sln"
confidence: observed-once
date: 2026-09-08
source-task: adhoc-roslyn-mcp-multi-solution
---

# A root you relativise against must go through the same canonicalisation as the paths you relativise

## Situation
roslyn-mcp maps each requested C# file to its owning `.sln` by walking up the
directory tree with `os.path.realpath`, then reports that solution as a path
relative to the server root (`ROSLYN_MCP_ROOT` or cwd). The root was used
raw. In the live end-to-end run the scratchpad root arrived as
`C:\Users\HUYTRU~1\AppData\Local\Temp\...` (an 8.3 short name from the
`TEMP` env var), while `realpath` expanded the solution path to
`C:\Users\HuyTruong\...`. `os.path.relpath` saw two different prefixes and
produced a nine-level `../../..` path, and the `solution == "repo-b/B.slnx"`
acceptance check failed.

## Lesson
Whenever a value is reported relative to a root, canonicalise the root with
exactly the same function you use on the paths (`os.path.realpath` for
`realpath`-resolved paths, `Path.resolve()` for `resolve()`-resolved ones)
at the single point where the root is read, and never use the raw env var or
cwd string afterwards. `relpath` only normalises `..` and case; it does not
expand 8.3 short names or symlinks, so any canonicalisation applied to one
side and not the other silently changes every relative path the tool emits.
Unit tests built on `tmp_path` will not catch this: pytest hands out the
already-long form of the temp dir. Pin it with a regression test that builds
a real short name via `GetShortPathNameW` (skip when the volume has 8.3 names
disabled) or a symlinked root, and always run at least one live check with the
root taken from an environment-supplied path rather than a test fixture.

## Evidence
`roslyn-mcp/src/roslyn_mcp/server.py` `_root()`: was
`os.environ.get("ROSLYN_MCP_ROOT") or os.getcwd()`; fixed by wrapping it in
`os.path.realpath(...)`. All 46 unit tests passed before the fix; the first
live `document_symbols("repo-b/src/LibB/Class1.cs")` against the real
`roslyn-language-server` returned `verdict: ok` but
`solution: ../../../../../../../../../HuyTruong/AppData/.../repo-b/B.slnx`.
Regression test `test_root_given_as_short_path_still_yields_clean_relative_paths`
in `roslyn-mcp/tests/test_server.py` creates a genuine short path with
`ctypes.windll.kernel32.GetShortPathNameW` and asserts `solution ==
"repo-b/B.sln"`. After the fix the live run reported `repo-b/B.slnx` and
all end-to-end checks passed in 28 s.

## Applies When / Not When
Applies to any tool that emits root-relative paths from a root supplied by
environment, config, or cwd — MCP servers in this repo (`amtcz-mcp`'s SARIF
and TRX shaping, `dbschema-mcp` if it ever reports files), CLI reporters, log
shaping. Most likely to bite on Windows (8.3 names in `%TEMP%`, `%USERPROFILE%`
with long names, case differences), and on any OS when the root or the files
sit behind a symlink (`/tmp` → `/private/tmp` on macOS). Does not apply when
both sides stay un-canonicalised and are only ever compared to each other, or
when paths are reported absolute.
