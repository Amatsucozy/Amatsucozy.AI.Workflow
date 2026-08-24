"""Tests for amtcz_mcp.trx — extract_trx_report() and run_test()."""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

from amtcz_mcp import trx

ZERO_DISCOVERED_TRX = """<?xml version="1.0" encoding="UTF-8"?>
<TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">
  <ResultSummary outcome="Completed">
    <Counters total="0" executed="0" passed="0" failed="0" />
  </ResultSummary>
</TestRun>
"""

PASS_ONLY_TRX = """<?xml version="1.0" encoding="UTF-8"?>
<TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">
  <TestDefinitions>
    <UnitTest name="Test_Passes" id="cccccccc-cccc-cccc-cccc-cccccccccccc">
      <TestMethod className="MyProject.Tests.SampleTests" name="Test_Passes" />
    </UnitTest>
  </TestDefinitions>
  <Results>
    <UnitTestResult testId="cccccccc-cccc-cccc-cccc-cccccccccccc" testName="Test_Passes" outcome="Passed" />
  </Results>
  <ResultSummary outcome="Passed">
    <Counters total="1" executed="1" passed="1" failed="0" />
  </ResultSummary>
</TestRun>
"""


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# --- extract_trx_report ------------------------------------------------


def test_extract_no_trx_nonexistent(tmp_path):
    report = trx.extract_trx_report(str(tmp_path / "missing.trx"), str(tmp_path), 25)
    assert report.verdict == "no_trx"


def test_extract_zero_discovered(tmp_path):
    path = tmp_path / "zero.trx"
    _write(str(path), ZERO_DISCOVERED_TRX)
    report = trx.extract_trx_report(str(path), str(tmp_path), 25)
    assert report.verdict == "zero_discovered"
    assert report.total == 0


def test_extract_pass(tmp_path):
    path = tmp_path / "pass.trx"
    _write(str(path), PASS_ONLY_TRX)
    report = trx.extract_trx_report(str(path), str(tmp_path), 25)
    assert report.verdict == "pass"
    assert report.total == 1
    assert report.passed == 1
    assert report.failed == 0


def test_extract_fail(tmp_path, fixtures_dir):
    src = os.path.join(fixtures_dir, "sample.trx")
    with open(src, encoding="utf-8") as f:
        content = f.read()
    path = tmp_path / "sample.trx"
    _write(str(path), content)

    report = trx.extract_trx_report(str(path), str(tmp_path), 25)

    assert report.verdict == "fail"
    assert report.total == 2
    assert report.passed == 1
    assert report.failed == 1
    assert len(report.failures) == 1
    failure = report.failures[0]
    assert failure.name == "Test_Fails"
    assert "Assert.Equal() Failure" in failure.message
    # Stack trace has "in src/SampleTests.cs:line 42" -> repo-relative frame.
    assert failure.location == ("src/SampleTests.cs", 42)


# --- run_test -------------------------------------------------------------


def _subprocess_writer(content, results_path):
    """Build a subprocess.run side_effect that writes `content` to
    `results_path`, simulating `dotnet test` producing a TRX file, then
    returns a returncode=0 result object."""

    def _side_effect(cmd, cwd=None, stdout=None, stderr=None):
        os.makedirs(os.path.dirname(results_path), exist_ok=True)
        with open(results_path, "w", encoding="utf-8") as f:
            f.write(content)
        return Mock(returncode=0)

    return _side_effect


def test_run_test_pass(tmp_path, fixtures_dir):
    results_dir = "TestResults/trx"
    results_path = os.path.join(str(tmp_path), results_dir, trx.TRX_FILENAME)

    with patch("amtcz_mcp.trx.which", return_value="/usr/bin/dotnet"), \
         patch("amtcz_mcp.trx.subprocess.run", side_effect=_subprocess_writer(PASS_ONLY_TRX, results_path)):
        result = trx.run_test(str(tmp_path), None, results_dir, False, None, 25)

    assert result.verdict == "pass"
    assert result.dotnet_found is True


def test_run_test_fail(tmp_path, fixtures_dir):
    results_dir = "TestResults/trx"
    results_path = os.path.join(str(tmp_path), results_dir, trx.TRX_FILENAME)
    with open(os.path.join(fixtures_dir, "sample.trx"), encoding="utf-8") as f:
        fail_content = f.read()

    with patch("amtcz_mcp.trx.which", return_value="/usr/bin/dotnet"), \
         patch("amtcz_mcp.trx.subprocess.run", side_effect=_subprocess_writer(fail_content, results_path)):
        result = trx.run_test(str(tmp_path), None, results_dir, False, None, 25)

    assert result.verdict == "fail"
    assert result.report is not None
    assert len(result.report.failures) == 1


def test_run_test_no_trx(tmp_path):
    results_dir = "TestResults/trx"

    def _no_file(cmd, cwd=None, stdout=None, stderr=None):
        return Mock(returncode=0)

    with patch("amtcz_mcp.trx.which", return_value="/usr/bin/dotnet"), \
         patch("amtcz_mcp.trx.subprocess.run", side_effect=_no_file):
        result = trx.run_test(str(tmp_path), None, results_dir, False, None, 25)

    assert result.verdict == "no_trx"


def test_run_test_dotnet_not_found(tmp_path):
    with patch("amtcz_mcp.trx.which", return_value=None):
        result = trx.run_test(str(tmp_path), None, "TestResults/trx", False, None, 25)

    assert result.verdict == "dotnet_not_found"
    assert result.dotnet_found is False
