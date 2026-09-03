"""amtcz-mcp server — exposes SARIF build, TRX test, and experience-memory
tools over MCP (stdio transport).

Successor to amtcz-cli's `amtcz sarif|test|exp ...` subcommands. Each tool
below wraps the pure-extraction/orchestration logic in sarif.py/trx.py/
experiences.py and returns a plain dict (dataclasses.asdict of the module's
result dataclass) instead of printing a table + exit code — the `verdict`
field is where the CLI's old exit-code semantics now live.
"""

from __future__ import annotations

import dataclasses
import os

from mcp.server.mcpserver import MCPServer

from amtcz_mcp import experiences, sarif, trx

mcp = MCPServer("amtcz")


@mcp.tool()
def sarif_build(
    root: str = ".",
    target: str | None = None,
    pattern: str = "**/obj/**/msbuild.sarif",
    max_rows: int = 30,
    warnings: bool = False,
    rebuild: bool = False,
) -> dict:
    """Run `dotnet build` with SARIF error logging and return a structured
    error-only report. Prefer this over sarif_probe when you need current
    results — sarif_probe only re-reads logs already on disk.

    verdict meanings:
      "success" - build succeeded, no compiler errors.
      "errors_found" - compiler errors are present; see report.errors
        (report.first_error is the one to fix first; report.cascade_verdict
        flags whether the rest look like fallout from it).
      "no_sarif_logs" - build ran but zero SARIF logs exist anywhere; the
        ErrorLog property was never applied. Infrastructure problem, not a
        code problem — don't retry with different flags, investigate the
        build setup instead.
      "gap_msbuild_failure" - the build failed (non-zero exit) but SARIF is
        clean/absent: the failure never reached the compiler (restore, SDK,
        bad project reference). Report console_tail to the human; don't
        retry.
      "dotnet_not_found" - `dotnet` is not on PATH. Environment problem,
        surface it to the human rather than retrying.

    rebuild=True deletes all SARIF logs first and passes --no-incremental,
    forcing a full recompile so every log is fresh. This is expensive — only
    use it on explicit human request (e.g. after a branch switch, or when
    carried/stale logs are suspected). Without rebuild, logs from projects
    MSBuild skipped as up-to-date are still valid and are reported as
    "carried" rather than "fresh".
    """
    result = sarif.run_sarif_build(root, target, pattern, max_rows, warnings, rebuild)
    return dataclasses.asdict(result)


@mcp.tool()
def sarif_probe(
    root: str = ".",
    pattern: str = "**/obj/**/msbuild.sarif",
    max_rows: int = 30,
    warnings: bool = False,
) -> dict:
    """Re-extract a report from SARIF logs already on disk, without
    rebuilding. Use this after a sarif_build whose output was truncated
    (raise max_rows) or to add warnings — never rebuild just to re-read the
    same logs.

    verdict meanings:
      "no_logs" - zero SARIF files found under root/pattern.
      "errors_found" - errors present after dedupe; see report fields
        (errors, first_error, cascade_verdict) same as sarif_build.
      "clean" - files were found but contain zero errors.
    """
    result = sarif.extract_sarif_report(root, pattern, max_rows, warnings)
    return dataclasses.asdict(result)


@mcp.tool()
def test_run(
    root: str = ".",
    target: str | None = None,
    results_dir: str = "TestResults/trx",
    no_build: bool = False,
    filter: str | None = None,
    max_rows: int = 25,
) -> dict:
    """Run `dotnet test` with TRX logging and return a structured
    failure-only report (passing tests are summarized as counts only, never
    listed). Prefer this over test_probe when tests haven't been run yet, or
    when code changed since the last run.

    verdict meanings:
      "pass" - all discovered tests passed (or there were zero failures).
      "fail" - one or more failures; see report.failures (each has name,
        class_, outcome, message, and location as (file, line) when a
        repo-relative stack frame could be resolved). report.cluster_verdict
        flags whether failures cluster around one exception type.
      "no_trx" - the TRX file is missing or unreadable/malformed after the
        run; treat as an infrastructure problem, not a test problem.
      "zero_discovered" - the run completed but discovered zero tests; check
        the target/filter, not the test code.
      "dotnet_not_found" - `dotnet` is not on PATH. Environment problem,
        surface it to the human rather than retrying.

    no_build=True skips the build step — use it right after a successful
    sarif_build (or another test_run) when the binaries are already fresh,
    to save time. filter uses `dotnet test --filter` expression syntax.
    """
    result = trx.run_test(root, target, results_dir, no_build, filter, max_rows)
    return dataclasses.asdict(result)


@mcp.tool()
def test_probe(
    root: str = ".",
    results_dir: str = "TestResults/trx",
    max_rows: int = 25,
) -> dict:
    """Re-read the existing TRX file without rerunning tests. Use this to
    re-extract with a different max_rows, or to inspect the last test_run's
    results again without paying for another `dotnet test` invocation —
    never rerun tests just to re-read the same TRX.

    verdict meanings: same as test_run ("pass", "fail", "no_trx",
    "zero_discovered") except "dotnet_not_found" cannot occur here (no
    process is launched).
    """
    trx_path = os.path.join(os.path.abspath(root), results_dir, trx.TRX_FILENAME)
    result = trx.extract_trx_report(trx_path, os.path.abspath(root), max_rows)
    return dataclasses.asdict(result)


@mcp.tool()
def exp_inventory(root: str = ".") -> dict:
    """List the experience-memory tag inventory (docs/experiences/*.md) as
    tag -> entry-count. This is CLAUDE.md's experience-routing step 1 —
    always call this before exp_search, so search tags come from the real
    inventory rather than an invented near-synonym.

    verdict meanings:
      "no_entries" - docs/experiences/ has zero entries and zero malformed
        files; nothing to route against, proceed as a FRESH problem.
      "ok" - entries exist; see tag_counts and entry_count. malformed lists
        any files missing a closed frontmatter block or a `slug` field —
        surfaced, never silently dropped.
    """
    result = experiences.inventory(root)
    return dataclasses.asdict(result)


@mcp.tool()
def exp_search(
    root: str = ".",
    tag: list[str] | None = None,
    symptom: str | None = None,
    keyword: list[str] | None = None,
    max_rows: int = 8,
) -> dict:
    """Search experience-memory entries by tag/symptom/keyword (CLAUDE.md
    experience-routing step 2). At least one of tag, symptom, or keyword is
    required. Never returns lesson bodies, only each hit's use_when column
    and path, by design — the caller decides which hits actually match their
    situation (via use_when) before reading the full file at path, rather
    than trusting a tag/keyword match alone.

    verdict meanings:
      "no_entries" - docs/experiences/ has zero entries and zero malformed
        files.
      "usage_error" - none of tag/symptom/keyword were given.
      "ok" - search ran; see hits (top max_rows, sorted by score then slug)
        and total_hits (may exceed len(hits) — see truncated). Zero hits is
        a valid, non-error outcome.
    """
    result = experiences.search(root, tag, symptom, keyword, max_rows)
    return dataclasses.asdict(result)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
