"""Tests for amtcz_mcp.experiences — inventory() and search()."""

from __future__ import annotations

from amtcz_mcp import experiences

EXPECTED_TAGS = {"pytest", "mocking", "dotnet", "sarif", "uri-parsing", "windows-paths"}


# --- inventory --------------------------------------------------------


def test_inventory_empty_dir(tmp_path):
    result = experiences.inventory(str(tmp_path))
    assert result.verdict == "no_entries"
    assert result.entry_count == 0


def test_inventory_with_fixtures(exp_root):
    result = experiences.inventory(exp_root)
    assert result.verdict == "ok"
    assert result.entry_count == 2
    assert set(result.tag_counts) == EXPECTED_TAGS
    assert all(count == 1 for count in result.tag_counts.values())
    assert len(result.malformed) == 1
    assert "malformed-entry" in result.malformed[0]


# --- search -------------------------------------------------------------


def test_search_empty_dir(tmp_path):
    result = experiences.search(str(tmp_path), tags=["pytest"], symptom=None, keywords=None, max_rows=8)
    assert result.verdict == "no_entries"


def test_search_usage_error(exp_root):
    result = experiences.search(exp_root, tags=None, symptom=None, keywords=None, max_rows=8)
    assert result.verdict == "usage_error"


def test_search_by_tag_discriminates(exp_root):
    result = experiences.search(exp_root, tags=["mocking"], symptom=None, keywords=None, max_rows=8)
    assert result.verdict == "ok"
    assert result.total_hits >= 1
    slugs = [hit.slug for hit in result.hits]
    assert "mcp-tool-testing" in slugs
    assert "sarif-uri-resolution" not in slugs


def test_search_by_keyword_full_text(exp_root):
    result = experiences.search(exp_root, tags=None, symptom=None, keywords=["urlparse"], max_rows=8)
    assert result.verdict == "ok"
    slugs = [hit.slug for hit in result.hits]
    assert "sarif-uri-resolution" in slugs
