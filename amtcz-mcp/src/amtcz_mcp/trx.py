"""dotnet test via TRX — pure extraction and test-run orchestration.

Vendored from amtcz-cli/amtcz.py (test section). No code sharing with
amtcz-cli: this is an independent copy, adapted to return dataclasses
instead of printing tables.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from shutil import which
from typing import Literal

TRX_NS = "{http://microsoft.com/schemas/VisualStudio/TeamTest/2010}"
TRX_FILENAME = "amtcz-results.trx"  # fixed name: stale-cleanup + probe rely on it
STACK_FRAME_RE = re.compile(r"in (?P<file>.+):line (?P<line>\d+)\s*$")
# TRX outcomes that are actual failures. NotExecuted (skipped) and
# Inconclusive are NOT failures - they ride in the summary's "other" count
# only; putting them in the table would flip a green suite to FAIL.
FAILURE_OUTCOMES = {"Failed", "Error", "Timeout", "Aborted"}


def _first_repo_frame(stack_trace: str, root: str):
    """First stack frame whose file resolves under root and isn't bin/obj
    generated output. Returns (rel_path, line) or None. Note: matches the
    invariant-culture ".. in <file>:line <n>" stack format; localized
    runtimes emit translated frames and fall through to [no repo frame]."""
    if not stack_trace:
        return None
    for line in stack_trace.splitlines():
        m = STACK_FRAME_RE.search(line.strip())
        if not m:
            continue
        raw = m.group("file")
        try:
            abs_path = os.path.abspath(
                raw if os.path.isabs(raw) else os.path.join(root, raw)
            )
        except ValueError:
            continue
        if (os.sep + "obj" + os.sep) in abs_path or (os.sep + "bin" + os.sep) in abs_path:
            continue
        try:
            rel = os.path.relpath(abs_path, root)
        except ValueError:
            continue
        if rel.startswith(".."):
            continue  # outside repo - a dependency's own source, not ours
        return rel.replace("\\", "/"), int(m.group("line"))
    return None


def _exception_type(message: str) -> str:
    """First clause before ':' - groups clusters the way sarif groups by
    CASCADE_CODES, but for exception types since TRX has no fixed
    diagnostic-code vocabulary."""
    if not message:
        return "?"
    head = message.strip().splitlines()[0]
    return head.split(":", 1)[0].strip() or "?"


def parse_trx_failures(path: str, root: str):
    """Yields dicts for every FAILURE result (see FAILURE_OUTCOMES):
    {name, class, outcome, message, location}. 'location' is (file, line)
    or None if no repo-relative stack frame was found."""
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError):
        # Unreadable TRX: pure data layer, no print — caller sees no
        # failures yielded from this file.
        return
    root_el = tree.getroot()

    class_by_id = {}
    for ut in root_el.findall(f".//{TRX_NS}TestDefinitions/{TRX_NS}UnitTest"):
        tid = ut.get("id")
        tm = ut.find(f"{TRX_NS}TestMethod")
        class_by_id[tid] = tm.get("className", "") if tm is not None else ""

    for r in root_el.findall(f".//{TRX_NS}Results/{TRX_NS}UnitTestResult"):
        outcome = r.get("outcome", "")
        if outcome not in FAILURE_OUTCOMES:
            continue
        msg_el = r.find(f"{TRX_NS}Output/{TRX_NS}ErrorInfo/{TRX_NS}Message")
        st_el = r.find(f"{TRX_NS}Output/{TRX_NS}ErrorInfo/{TRX_NS}StackTrace")
        message = " ".join((msg_el.text or "").split()) if msg_el is not None else ""
        stack = (st_el.text or "") if st_el is not None else ""
        yield {
            "name": r.get("testName", "?"),
            "class": class_by_id.get(r.get("testId"), ""),
            "outcome": outcome,
            "message": message,
            "location": _first_repo_frame(stack, root),
        }


def read_trx_summary(path: str):
    """Returns (total, passed, failed, other) from ResultSummary/Counters,
    or None if unreadable/malformed."""
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError):
        return None
    counters = tree.getroot().find(f".//{TRX_NS}ResultSummary/{TRX_NS}Counters")
    if counters is None:
        return None
    total = int(counters.get("total", 0))
    passed = int(counters.get("passed", 0))
    failed = int(counters.get("failed", 0))
    other = total - passed - failed
    return total, passed, failed, other


@dataclass
class TrxFailure:
    name: str
    class_: str
    outcome: str
    message: str
    location: tuple[str, int] | None


@dataclass
class TrxReport:
    verdict: Literal["no_trx", "zero_discovered", "pass", "fail"]
    total: int = 0
    passed: int = 0
    failed: int = 0
    other: int = 0
    failures: list[TrxFailure] = field(default_factory=list)
    truncated: bool = False
    cluster_verdict: str | None = None


def extract_trx_report(trx_path: str, root: str, max_rows: int) -> TrxReport:
    """Report core, shared by test-run and test-probe tools.
    Verdict meaning: no_trx = file missing or unreadable/malformed
    ResultSummary (old exit 2, two distinct original causes collapsed into
    one verdict), zero_discovered = total == 0 (old exit 3), fail = any
    failures parsed (old exit 1), pass = otherwise (old exit 0)."""
    if not os.path.exists(trx_path):
        return TrxReport(verdict="no_trx")

    summary = read_trx_summary(trx_path)
    if summary is None:
        return TrxReport(verdict="no_trx")
    total, passed, failed, other = summary

    if total == 0:
        return TrxReport(verdict="zero_discovered", total=total, passed=passed,
                          failed=failed, other=other)

    failures_raw = list(parse_trx_failures(trx_path, root))
    failures = [TrxFailure(name=f["name"], class_=f["class"], outcome=f["outcome"],
                            message=f["message"], location=f["location"])
                for f in failures_raw]

    if not failures:
        return TrxReport(verdict="pass", total=total, passed=passed,
                          failed=failed, other=other)

    truncated = len(failures) > max_rows

    cluster_verdict = None
    if len(failures) > 1:
        types = [_exception_type(f.message) for f in failures]
        top_type, top_count = max(
            ((t, types.count(t)) for t in set(types)), key=lambda kv: kv[1]
        )
        if top_count >= max(2, len(failures) // 2):
            cluster_verdict = f"{top_count}/{len(failures)} failures are {top_type}"
        else:
            cluster_verdict = "none - mostly independent failures"

    return TrxReport(
        verdict="fail",
        total=total,
        passed=passed,
        failed=failed,
        other=other,
        failures=failures,
        truncated=truncated,
        cluster_verdict=cluster_verdict,
    )


@dataclass
class TestRunResult:
    test_exit: int
    dotnet_found: bool
    console_tail: list[str] = field(default_factory=list)
    report: TrxReport | None = None
    verdict: Literal["pass", "fail", "no_trx", "zero_discovered", "dotnet_not_found"] = "pass"


def run_test(root: str, target: str | None, results_dir: str, no_build: bool,
             filter_expr: str | None, max_rows: int) -> TestRunResult:
    if which("dotnet") is None:
        return TestRunResult(test_exit=-1, dotnet_found=False, verdict="dotnet_not_found")

    abs_results_dir = os.path.join(root, results_dir)
    os.makedirs(abs_results_dir, exist_ok=True)
    stale = os.path.join(abs_results_dir, TRX_FILENAME)
    if os.path.exists(stale):
        os.remove(stale)

    cmd = ["dotnet", "test"]
    if target:
        cmd.append(target)
    if no_build:
        cmd.append("--no-build")
    if filter_expr:
        cmd += ["--filter", filter_expr]
    cmd += [
        "-v", "q", "--nologo",
        "--logger", f"trx;LogFileName={TRX_FILENAME}",
        "--results-directory", abs_results_dir,
    ]

    console = os.path.join(tempfile.gettempdir(), "amtcz-mcp-test-console.txt")
    with open(console, "w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run(cmd, cwd=root, stdout=f, stderr=subprocess.STDOUT)

    console_tail: list[str] = []
    try:
        with open(console, encoding="utf-8", errors="replace") as f:
            console_tail = f.read().splitlines()[-8:]
    except OSError:
        pass

    report = extract_trx_report(os.path.join(abs_results_dir, TRX_FILENAME), root, max_rows)

    return TestRunResult(
        test_exit=proc.returncode,
        dotnet_found=True,
        console_tail=console_tail,
        report=report,
        verdict=report.verdict,
    )
