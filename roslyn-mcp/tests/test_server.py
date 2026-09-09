"""Tests for roslyn_mcp.server — tool registration, the verdict contract, and
multi-solution routing driven through the real tool functions.

The `mcp` high-level server's tool() decorator returns the original function
unchanged, so every tool is directly callable. The module-level ClientPool is
swapped for one that builds FakeClient instances: no Roslyn process is ever
spawned, and `request` answers with empty LSP results.
"""

from __future__ import annotations

import asyncio
import os
import sys

import pytest

from roslyn_mcp import server
from roslyn_mcp.lsp_client import default_log_dir, path_to_uri
from roslyn_mcp.workspaces import ClientPool

EXPECTED_TOOL_NAMES = [
    "definition",
    "diagnostics",
    "document_symbols",
    "hover",
    "implementations",
    "references",
    "refresh_file",
    "rename_preview",
    "workspace_status",
]


class FakeClient:
    def __init__(self, root, solution=None, fail_start=False):
        self.root = root
        self.solution = solution
        self.log_dir = default_log_dir(root, solution)
        self.alive = False
        self.ready = False
        self.exit_code = None
        self.started = 0
        self.opened: list[str] = []
        self._fail = fail_start

    def start(self):
        if self._fail:
            raise FileNotFoundError("'roslyn-language-server' not found on PATH")
        self.alive = self.ready = True
        self.started += 1

    def wait_ready(self, timeout=0):
        return self.ready

    def shutdown(self):
        self.alive = self.ready = False

    def uptime(self):
        return 1.0

    def open(self, path):
        self.opened.append(path)
        return path_to_uri(path)

    refresh = open

    def request(self, method, params, timeout=None):
        return []


def _touch(path, text=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


@pytest.fixture
def root(tmp_path, monkeypatch):
    """Isolated server root with a fake, 2-slot client pool."""
    monkeypatch.setenv("ROSLYN_MCP_ROOT", str(tmp_path))
    monkeypatch.delenv("ROSLYN_MCP_SOLUTION", raising=False)
    monkeypatch.delenv("ROSLYN_MCP_MAX_WORKSPACES", raising=False)
    monkeypatch.setattr(server, "_pool", ClientPool(2, lambda s: FakeClient(str(tmp_path), s)))
    return tmp_path


def _solutions_loaded():
    return [server._rel_root(c.solution) for c in server._pool.loaded()]


# ------------------------------------------------------------ contract

def test_list_tools_names():
    names = sorted(t.name for t in asyncio.run(server.mcp.list_tools()))
    assert names == EXPECTED_TOOL_NAMES


def test_workspace_status_exposes_solution_parameter():
    tool = next(t for t in asyncio.run(server.mcp.list_tools()) if t.name == "workspace_status")
    schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", {})
    assert {"wait_seconds", "solution"} <= set(schema.get("properties", {}))


def test_every_tool_returns_plain_dict_with_verdict(root):
    _touch(root / "A.sln")
    f = _touch(root / "src" / "X.cs", "class X {}")
    calls = [
        lambda: server.document_symbols("src/X.cs"),
        lambda: server.definition("src/X.cs", 1, 7),
        lambda: server.implementations("src/X.cs", 1, 7),
        lambda: server.references("src/X.cs", 1, 7),
        lambda: server.hover("src/X.cs", 1, 7),
        lambda: server.diagnostics("src/X.cs"),
        lambda: server.rename_preview("src/X.cs", 1, 7, "Y"),
        lambda: server.refresh_file("src/X.cs"),
        lambda: server.workspace_status(),
    ]
    for call in calls:
        r = call()
        assert isinstance(r, dict) and not hasattr(r, "__dataclass_fields__")
        assert r["verdict"] == "ok", r
        assert r["solution"] == "A.sln"
        # verdict must be the FIRST key: clients that truncate long payloads
        # (hundreds of symbols/references) would otherwise never see it.
        assert list(r)[:2] == ["verdict", "solution"], list(r)


def test_loading_hint_precedes_payload(root):
    _touch(root / "A.sln")
    _touch(root / "src" / "X.cs", "class X {}")
    c = server._pool.get(str(root / "A.sln"))
    c.ready = False
    r = server.document_symbols("src/X.cs")
    assert list(r)[:3] == ["verdict", "solution", "hint"] and r["verdict"] == "workspace_loading"


def test_missing_file_is_a_verdict_not_an_exception(root):
    _touch(root / "A.sln")
    r = server.document_symbols("src/Nope.cs")
    assert r["verdict"] == "file_not_found" and "Nope.cs" in r["error"]
    assert _solutions_loaded() == []  # nothing spawned for a bad path


# ------------------------------------------------------------ routing

def test_single_solution_root_routes_without_workspace_status(root):
    _touch(root / "A.sln")
    _touch(root / "src" / "X.cs", "class X {}")
    r = server.document_symbols("src/X.cs")
    assert r["verdict"] == "ok" and r["solution"] == "A.sln" and r["symbols"] == []
    assert _solutions_loaded() == ["A.sln"]


def test_multi_repo_root_auto_resolves_nearest_solution(root):
    _touch(root / "repo-a" / "A.sln")
    _touch(root / "repo-b" / "B.sln")
    _touch(root / "repo-b" / "src" / "X.cs", "class X {}")
    _touch(root / "repo-a" / "src" / "Y.cs", "class Y {}")
    r = server.document_symbols("repo-b/src/X.cs")
    assert r["verdict"] == "ok" and r["solution"] == "repo-b/B.sln"
    assert _solutions_loaded() == ["repo-b/B.sln"]
    c = server._pool.loaded()[0]
    assert c.log_dir == os.path.join(str(root), ".roslyn-mcp", "B")
    r = server.hover("repo-a/src/Y.cs", 1, 7)
    assert r["verdict"] == "ok" and r["solution"] == "repo-a/A.sln"
    assert _solutions_loaded() == ["repo-b/B.sln", "repo-a/A.sln"]


def test_two_solutions_same_dir_unselected_then_status_selects(root):
    _touch(root / "A.sln")
    _touch(root / "B.sln")
    _touch(root / "src" / "X.cs", "class X {}")
    r = server.document_symbols("src/X.cs")
    assert r["verdict"] == "workspace_unselected"
    assert r["candidates"] == ["A.sln", "B.sln"]
    assert "workspace_status" in r["hint"]
    assert _solutions_loaded() == []
    s = server.workspace_status(solution="B.sln")
    assert s["verdict"] == "ok" and s["solution"] == "B.sln"
    r = server.document_symbols("src/X.cs")
    assert r["verdict"] == "ok" and r["solution"] == "B.sln"
    assert _solutions_loaded() == ["B.sln"]


def test_ambiguous_file_follows_most_recent_selection(root):
    _touch(root / "A.sln")
    _touch(root / "B.sln")
    _touch(root / "src" / "X.cs", "class X {}")
    server.workspace_status(solution="A.sln")
    server.workspace_status(solution="B.sln")
    assert server.document_symbols("src/X.cs")["solution"] == "B.sln"
    server.workspace_status(solution="A.sln")
    assert server.document_symbols("src/X.cs")["solution"] == "A.sln"


def test_file_with_no_owning_solution_offers_root_candidates(root):
    _touch(root / "repo-a" / "A.sln")
    _touch(root / "repo-b" / "B.sln")
    _touch(root / "shared" / "S.cs", "class S {}")
    r = server.document_symbols("shared/S.cs")
    assert r["verdict"] == "workspace_unselected"
    assert r["candidates"] == ["repo-a/A.sln", "repo-b/B.sln"]


def test_root_without_any_solution_falls_back_to_autoload(root):
    _touch(root / "src" / "X.cs", "class X {}")
    r = server.document_symbols("src/X.cs")
    assert r["verdict"] == "ok" and r["solution"] is None
    assert server._pool.loaded()[0].solution is None
    s = server.workspace_status()
    assert s["verdict"] == "ok" and s["solutions"] == [] and s["solution"] is None


def test_lru_eviction_shuts_down_oldest_workspace(root):
    for name in "abc":
        _touch(root / f"repo-{name}" / f"{name.upper()}.sln")
        _touch(root / f"repo-{name}" / "X.cs", "class X {}")
    server.document_symbols("repo-a/X.cs")
    server.document_symbols("repo-b/X.cs")
    a = server._pool.loaded()[0]
    server.document_symbols("repo-c/X.cs")
    assert not a.alive and _solutions_loaded() == ["repo-b/B.sln", "repo-c/C.sln"]


# ------------------------------------------------------------ escape hatch

def test_forced_solution_skips_discovery_and_routes_everything(root, monkeypatch):
    _touch(root / "repo-a" / "A.sln")
    _touch(root / "repo-b" / "B.sln")
    _touch(root / "repo-b" / "src" / "X.cs", "class X {}")
    monkeypatch.setenv("ROSLYN_MCP_SOLUTION", "repo-a/A.sln")

    def no_scan(*a, **k):
        raise AssertionError("discovery must not run when ROSLYN_MCP_SOLUTION is set")
    monkeypatch.setattr(server, "discover_solutions", no_scan)

    s = server.workspace_status()
    assert s["verdict"] == "ok" and s["solutions"] == ["repo-a/A.sln"] and s["pinned"] is True
    r = server.document_symbols("repo-b/src/X.cs")  # would resolve to B without the pin
    assert r["verdict"] == "ok" and r["solution"] == "repo-a/A.sln"
    assert _solutions_loaded() == ["repo-a/A.sln"]


# ------------------------------------------------------------ workspace_status

def test_status_with_no_clients_and_several_solutions_is_unselected(root):
    _touch(root / "repo-a" / "A.sln")
    _touch(root / "repo-b" / "B.sln")
    s = server.workspace_status()
    assert s["verdict"] == "workspace_unselected"
    assert s["candidates"] == ["repo-a/A.sln", "repo-b/B.sln"] and s["workspaces"] == []
    assert _solutions_loaded() == []


def test_status_with_single_solution_opens_it(root):
    _touch(root / "repo-a" / "A.sln")
    s = server.workspace_status(wait_seconds=5)
    assert s["verdict"] == "ok" and s["solution"] == "repo-a/A.sln" and s["ready"] is True
    assert s["solutions"] == ["repo-a/A.sln"]
    assert [w["solution"] for w in s["workspaces"]] == ["repo-a/A.sln"]


def test_status_reports_all_loaded_workspaces(root):
    _touch(root / "repo-a" / "A.sln")
    _touch(root / "repo-b" / "B.sln")
    server.workspace_status(solution="repo-a/A.sln")
    server.workspace_status(solution="repo-b/B.sln")
    s = server.workspace_status()
    assert s["solution"] == "repo-b/B.sln"  # most recently selected stays current
    assert [w["solution"] for w in s["workspaces"]] == ["repo-a/A.sln", "repo-b/B.sln"]
    assert s["max_workspaces"] == 2


def test_status_unknown_solution_is_file_not_found(root):
    _touch(root / "A.sln")
    s = server.workspace_status(solution="Nope.sln")
    assert s["verdict"] == "file_not_found" and _solutions_loaded() == []


def test_status_restarts_dead_current_workspace(root):
    _touch(root / "A.sln")
    first = server._pool.get(str(root / "A.sln"))
    first.alive = first.ready = False
    s = server.workspace_status()
    assert s["verdict"] == "ok" and s["alive"] is True
    assert server._pool.loaded()[0] is not first


def test_launch_failure_is_server_dead_everywhere(root, monkeypatch):
    _touch(root / "A.sln")
    _touch(root / "src" / "X.cs", "class X {}")
    monkeypatch.setattr(server, "_pool",
                        ClientPool(2, lambda s: FakeClient(str(root), s, fail_start=True)))
    assert server.workspace_status()["verdict"] == "server_dead"
    r = server.document_symbols("src/X.cs")
    assert r["verdict"] == "server_dead" and "not found" in r["error"]
    assert _solutions_loaded() == []


@pytest.mark.skipif(sys.platform != "win32", reason="8.3 short names are a Windows thing")
def test_root_given_as_short_path_still_yields_clean_relative_paths(tmp_path, monkeypatch):
    """Regression: ROSLYN_MCP_ROOT=C:\\Users\\HUYTRU~1\\... while the resolved
    solution path used the long name, so `solution` came back as ../../../…"""
    import ctypes
    long_dir = tmp_path / "long directory name"
    long_dir.mkdir()
    buf = ctypes.create_unicode_buffer(512)
    ctypes.windll.kernel32.GetShortPathNameW(str(long_dir), buf, 512)
    short = buf.value
    if not short or short.lower() == str(long_dir).lower():
        pytest.skip("volume has 8.3 names disabled")
    monkeypatch.setenv("ROSLYN_MCP_ROOT", short)
    monkeypatch.setattr(server, "_pool", ClientPool(2, lambda s: FakeClient(server._root(), s)))
    _touch(long_dir / "repo-b" / "B.sln")
    _touch(long_dir / "repo-b" / "src" / "X.cs", "class X {}")
    r = server.document_symbols("repo-b/src/X.cs")
    assert r["verdict"] == "ok" and r["solution"] == "repo-b/B.sln", r
    assert r["file"] == "repo-b/src/X.cs"
    assert server.workspace_status()["solutions"] == ["repo-b/B.sln"]


def test_max_workspaces_env_is_honoured(monkeypatch):
    monkeypatch.setenv("ROSLYN_MCP_MAX_WORKSPACES", "3")
    assert server._new_pool().max_size == 3
    monkeypatch.setenv("ROSLYN_MCP_MAX_WORKSPACES", "garbage")
    assert server._new_pool().max_size == server.DEFAULT_MAX_WORKSPACES
