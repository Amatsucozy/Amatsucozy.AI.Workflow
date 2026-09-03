"""SARIF build diagnostics — pure extraction and build orchestration.

Vendored from amtcz-cli/amtcz.py (sarif section). No code sharing with
amtcz-cli: this is an independent copy, adapted to return dataclasses
instead of printing tables.
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import unquote, urlparse

# Codes that usually cascade from an earlier missing-type/namespace failure.
CASCADE_CODES = {"CS0246", "CS0234", "CS0400", "CS0103", "CS1061", "CS0117",
                 "CS0115", "CS0538", "CS0535"}

BUILD_PROPERTY = "-p:ErrorLog=obj/msbuild.sarif%2Cversion=2.1"


def uri_to_rel(uri: str, root: str) -> str:
    if not uri:
        return "<no file>"
    if uri.startswith("file:"):
        p = unquote(urlparse(uri).path)
        # windows file URIs arrive as /C:/...
        if len(p) > 2 and p[0] == "/" and p[2] == ":":
            p = p[1:]
    else:
        p = unquote(uri)
    try:
        rel = os.path.relpath(os.path.abspath(p), root)
    except ValueError:  # different drive on windows
        rel = p
    return rel.replace("\\", "/")


def load_diagnostics(path: str, root: str):
    try:
        with open(path, encoding="utf-8-sig") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError):
        # Unreadable SARIF file: pure data layer, no print — caller sees
        # simply no diagnostics contributed from this file.
        return
    for run in doc.get("runs", []):
        for res in run.get("results", []):
            loc = (res.get("locations") or [{}])[0].get("physicalLocation", {})
            region = loc.get("region", {})
            msg = " ".join((res.get("message", {}).get("text") or "").split())
            yield {
                "level": res.get("level", "warning"),
                "code": res.get("ruleId") or "?",
                "file": uri_to_rel(loc.get("artifactLocation", {}).get("uri"), root),
                "line": region.get("startLine", 0),
                "msg": msg,
            }


def find_sarif_files(root: str, pattern: str):
    """All SARIF logs under root matching pattern (bin/ excluded), sorted by
    mtime — compile sequence proxy: earlier project first."""
    return sorted(
        (p for p in glob.glob(os.path.join(root, pattern), recursive=True)
         if os.sep + "bin" + os.sep not in p),
        key=os.path.getmtime,
    )


@dataclass
class SarifDiagnostic:
    level: str
    code: str
    file: str
    line: int
    msg: str


@dataclass
class SarifReport:
    log_count: int
    verdict: Literal["no_logs", "clean", "errors_found"]
    errors: list[SarifDiagnostic] = field(default_factory=list)
    warnings: list[SarifDiagnostic] = field(default_factory=list)
    total_errors: int = 0
    truncated: bool = False
    first_error: SarifDiagnostic | None = None
    cascade_count: int = 0
    cascade_verdict: str | None = None


def extract_sarif_report(root: str, pattern: str, max_rows: int, include_warnings: bool) -> SarifReport:
    """Extraction core, shared by sarif-probe and sarif-build tools.
    Verdict meaning: no_logs = zero SARIF files found (old exit 2),
    errors_found = any errors after dedupe (old exit 1),
    clean = otherwise, including files found but zero errors (old exit 0)."""
    files = find_sarif_files(root, pattern)
    if not files:
        return SarifReport(log_count=0, verdict="no_logs")

    seen, errors_raw, warnings_raw = set(), [], []
    for path in files:
        for d in load_diagnostics(path, root):
            key = (d["code"], d["file"], d["line"], d["msg"])
            if key in seen:  # multi-target / multi-run duplicates
                continue
            seen.add(key)
            (errors_raw if d["level"] == "error" else warnings_raw).append(d)

    errors = [SarifDiagnostic(**d) for d in errors_raw]
    warnings = [SarifDiagnostic(**d) for d in warnings_raw] if include_warnings else []

    truncated = len(errors) > max_rows
    first_error = errors[0] if errors else None

    cascade_count = 0
    cascade_verdict = None
    if errors:
        tail = errors[1:]
        cascade_count = sum(1 for d in tail if d.code in CASCADE_CODES)
        if tail:
            cascade_verdict = ("likely cascade - fix #1 first"
                                if cascade_count >= max(1, len(tail) // 2)
                                else "mostly independent errors")

    verdict: Literal["clean", "errors_found"] = "errors_found" if errors else "clean"

    return SarifReport(
        log_count=len(files),
        verdict=verdict,
        errors=errors,
        warnings=warnings,
        total_errors=len(errors),
        truncated=truncated,
        first_error=first_error,
        cascade_count=cascade_count,
        cascade_verdict=cascade_verdict,
    )


def clean_all_sarif(root: str, pattern: str) -> int:
    """Delete every matching SARIF log. Used ONLY with rebuild=True: deleting
    logs without forcing recompile recreates the incremental-skip gap
    (compile skipped -> no new log -> false 'no SARIF found')."""
    removed = 0
    for p in find_sarif_files(root, pattern):
        try:
            os.remove(p)
            removed += 1
        except OSError:
            pass
    return removed


@dataclass
class SarifBuildResult:
    build_exit: int
    dotnet_found: bool
    console_tail: list[str] = field(default_factory=list)
    logs_fresh: int = 0
    logs_carried: int = 0
    report: SarifReport | None = None
    verdict: Literal["success", "errors_found", "no_sarif_logs",
                      "gap_msbuild_failure", "dotnet_not_found"] = "success"


def run_sarif_build(root: str, target: str | None, pattern: str, max_rows: int,
                     include_warnings: bool, rebuild: bool) -> SarifBuildResult:
    if rebuild:
        clean_all_sarif(root, pattern)
        before = {}
    else:
        # Incremental-safe: do NOT delete logs. MSBuild skips CSC for
        # up-to-date projects and CSC is what writes SARIF — a log whose
        # compile was skipped is still valid (inputs unchanged since it
        # was written). Snapshot mtimes to report fresh vs carried.
        before = {p: os.path.getmtime(p) for p in find_sarif_files(root, pattern)}

    console = os.path.join(tempfile.gettempdir(), "amtcz-mcp-build-console.txt")
    cmd = ["dotnet", "build"]
    if target:
        cmd.append(target)
    if rebuild:
        cmd.append("--no-incremental")
    cmd += ["-v", "q", "-nologo", BUILD_PROPERTY]

    try:
        with open(console, "w", encoding="utf-8", errors="replace") as f:
            proc = subprocess.run(cmd, cwd=root, stdout=f, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        return SarifBuildResult(build_exit=-1, dotnet_found=False, verdict="dotnet_not_found")

    console_tail: list[str] = []
    try:
        with open(console, encoding="utf-8", errors="replace") as f:
            console_tail = f.read().splitlines()[-8:]
    except OSError:
        pass

    after = find_sarif_files(root, pattern)
    fresh = [p for p in after if p not in before or os.path.getmtime(p) > before[p]]
    carried = len(after) - len(fresh)

    report = extract_sarif_report(root, pattern, max_rows, include_warnings)

    if report.verdict == "errors_found":
        verdict: Literal["success", "errors_found", "no_sarif_logs",
                          "gap_msbuild_failure", "dotnet_not_found"] = "errors_found"
    elif proc.returncode != 0:
        # build failed yet SARIF is clean/absent: the failure never reached
        # the compiler (restore, SDK, bad project reference).
        verdict = "gap_msbuild_failure"
    elif report.verdict == "no_logs":
        # build succeeded yet zero logs exist anywhere (none fresh, none
        # carried) - the ErrorLog property genuinely was not applied.
        verdict = "no_sarif_logs"
    else:
        verdict = "success"

    return SarifBuildResult(
        build_exit=proc.returncode,
        dotnet_found=True,
        console_tail=console_tail,
        logs_fresh=len(fresh),
        logs_carried=carried,
        report=report,
        verdict=verdict,
    )
