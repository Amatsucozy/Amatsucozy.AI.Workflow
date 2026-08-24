"""Tests for amtcz_mcp.sarif — extract_sarif_report() and run_sarif_build()."""

from __future__ import annotations

import os
import shutil
from unittest.mock import Mock, patch

from amtcz_mcp import sarif

CLEAN_SARIF = """{
  "version": "2.1.0",
  "runs": [
    {
      "tool": {"driver": {"name": "csc", "rules": []}},
      "results": []
    }
  ]
}
"""


def _write_clean_sarif(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(CLEAN_SARIF)


# --- extract_sarif_report -------------------------------------------------


def test_extract_no_sarif_files(tmp_path):
    report = sarif.extract_sarif_report(str(tmp_path), "*.sarif", 30, False)
    assert report.verdict == "no_logs"
    assert report.log_count == 0


def test_extract_clean_dir(tmp_path):
    _write_clean_sarif(tmp_path / "clean.sarif")
    report = sarif.extract_sarif_report(str(tmp_path), "*.sarif", 30, False)
    assert report.verdict == "clean"
    assert report.total_errors == 0


def test_extract_errors_found(tmp_path, fixtures_dir):
    shutil.copy(os.path.join(fixtures_dir, "sample.sarif"), tmp_path / "sample.sarif")
    report = sarif.extract_sarif_report(str(tmp_path), "*.sarif", 30, False)
    assert report.verdict == "errors_found"
    assert report.total_errors == 1
    assert report.first_error is not None
    assert report.first_error.code == "CS0246"


def test_extract_include_warnings_true(tmp_path, fixtures_dir):
    shutil.copy(os.path.join(fixtures_dir, "sample.sarif"), tmp_path / "sample.sarif")
    report = sarif.extract_sarif_report(str(tmp_path), "*.sarif", 30, True)
    assert len(report.warnings) == 1
    assert report.warnings[0].code == "CS0168"


def test_extract_include_warnings_false(tmp_path, fixtures_dir):
    shutil.copy(os.path.join(fixtures_dir, "sample.sarif"), tmp_path / "sample.sarif")
    report = sarif.extract_sarif_report(str(tmp_path), "*.sarif", 30, False)
    assert report.warnings == []


def test_extract_truncated_at_max_rows_zero(tmp_path, fixtures_dir):
    shutil.copy(os.path.join(fixtures_dir, "sample.sarif"), tmp_path / "sample.sarif")
    # Fixture has exactly 1 error; max_rows=0 forces len(errors) > max_rows.
    report = sarif.extract_sarif_report(str(tmp_path), "*.sarif", 0, False)
    assert report.total_errors == 1
    assert report.truncated is True


def test_extract_not_truncated_at_max_rows_one(tmp_path, fixtures_dir):
    shutil.copy(os.path.join(fixtures_dir, "sample.sarif"), tmp_path / "sample.sarif")
    # 1 error is not > max_rows=1, so truncated must be False.
    report = sarif.extract_sarif_report(str(tmp_path), "*.sarif", 1, False)
    assert report.total_errors == 1
    assert report.truncated is False


# --- run_sarif_build --------------------------------------------------------

DEFAULT_PATTERN = "**/obj/**/msbuild.sarif"


def _place_sarif(tmp_path, content):
    obj_dir = tmp_path / "obj"
    obj_dir.mkdir(parents=True, exist_ok=True)
    path = obj_dir / "msbuild.sarif"
    path.write_text(content, encoding="utf-8")
    return path


def test_run_sarif_build_errors_found(tmp_path, fixtures_dir):
    with open(os.path.join(fixtures_dir, "sample.sarif"), encoding="utf-8") as f:
        error_sarif = f.read()
    _place_sarif(tmp_path, error_sarif)

    with patch("amtcz_mcp.sarif.subprocess.run", return_value=Mock(returncode=0)):
        result = sarif.run_sarif_build(str(tmp_path), None, DEFAULT_PATTERN, 30, False, False)

    assert result.verdict == "errors_found"


def test_run_sarif_build_no_sarif_logs(tmp_path):
    with patch("amtcz_mcp.sarif.subprocess.run", return_value=Mock(returncode=0)):
        result = sarif.run_sarif_build(str(tmp_path), None, DEFAULT_PATTERN, 30, False, False)

    assert result.verdict == "no_sarif_logs"


def test_run_sarif_build_gap_msbuild_failure(tmp_path):
    _place_sarif(tmp_path, CLEAN_SARIF)

    with patch("amtcz_mcp.sarif.subprocess.run", return_value=Mock(returncode=1)):
        result = sarif.run_sarif_build(str(tmp_path), None, DEFAULT_PATTERN, 30, False, False)

    assert result.verdict == "gap_msbuild_failure"


def test_run_sarif_build_success(tmp_path):
    _place_sarif(tmp_path, CLEAN_SARIF)

    with patch("amtcz_mcp.sarif.subprocess.run", return_value=Mock(returncode=0)):
        result = sarif.run_sarif_build(str(tmp_path), None, DEFAULT_PATTERN, 30, False, False)

    assert result.verdict == "success"


def test_run_sarif_build_dotnet_not_found(tmp_path):
    with patch("amtcz_mcp.sarif.subprocess.run", side_effect=FileNotFoundError):
        result = sarif.run_sarif_build(str(tmp_path), None, DEFAULT_PATTERN, 30, False, False)

    assert result.verdict == "dotnet_not_found"
    assert result.dotnet_found is False
