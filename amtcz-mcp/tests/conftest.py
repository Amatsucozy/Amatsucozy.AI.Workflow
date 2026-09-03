"""Shared pytest fixtures for the amtcz-mcp test suite."""

from __future__ import annotations

import os
import shutil

import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixtures_dir() -> str:
    """Absolute path to amtcz-mcp/tests/fixtures/."""
    return FIXTURES_DIR


@pytest.fixture
def exp_root(tmp_path, fixtures_dir) -> str:
    """A tmp_path root with docs/experiences/*.md populated from
    fixtures/experiences/ — matches the root/docs/experiences/*.md layout
    that experiences.load_entries() expects (it globs relative to root, not
    the fixtures dir directly)."""
    target = tmp_path / "docs" / "experiences"
    target.mkdir(parents=True)
    src = os.path.join(fixtures_dir, "experiences")
    for name in os.listdir(src):
        shutil.copy(os.path.join(src, name), target / name)
    return str(tmp_path)
