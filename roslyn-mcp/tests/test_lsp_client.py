"""Tests for the RoslynClient handshake with a fake transport — no process is
spawned. Covers the explicit-solution flow (`solution/open` after
`initialized`, no `--autoLoadProjects`) and the auto-load fallback."""

from __future__ import annotations

import os

from roslyn_mcp.lsp_client import (
    LOG_DIR_NAME, SOLUTION_OPEN, RoslynClient, default_log_dir, path_to_uri,
)


def _fake_handshake(c: RoslynClient) -> list[dict]:
    """Stub the wire: `request` answers `initialize` synchronously, `_send`
    records every outgoing message."""
    sent: list[dict] = []
    c._send = lambda m: sent.append(m)
    c.request = lambda method, params, timeout=None: (
        sent.append({"method": method, "params": params}) or {"capabilities": {"x": 1}})
    return sent


def test_explicit_solution_sends_solution_open_after_initialized(tmp_path):
    sln = tmp_path / "repo-b" / "B.sln"
    sln.parent.mkdir()
    sln.write_text("")
    c = RoslynClient(str(tmp_path), solution=str(sln))
    sent = _fake_handshake(c)
    c._initialize()
    methods = [m["method"] for m in sent]
    assert methods == ["initialize", "initialized", SOLUTION_OPEN]
    assert sent[2]["params"] == {"solution": path_to_uri(sln)}
    assert c.server_capabilities == {"x": 1}
    # The LSP workspace folder is the solution's directory, not the multi-repo root.
    init = sent[0]["params"]
    assert init["rootUri"] == path_to_uri(sln.parent)
    assert init["workspaceFolders"] == [{"uri": path_to_uri(sln.parent), "name": "repo-b"}]


def test_autoload_fallback_sends_no_solution_open(tmp_path):
    c = RoslynClient(str(tmp_path))
    sent = _fake_handshake(c)
    c._initialize()
    assert [m["method"] for m in sent] == ["initialize", "initialized"]
    assert sent[0]["params"]["rootUri"] == path_to_uri(tmp_path)


def test_launch_args_drop_autoload_when_solution_known(tmp_path):
    with_sln = RoslynClient(str(tmp_path), solution="A.sln")
    without = RoslynClient(str(tmp_path))
    assert "--autoLoadProjects" not in with_sln.launch_args("exe")
    assert "--autoLoadProjects" in without.launch_args("exe")
    assert with_sln.launch_args("exe")[:2] == ["exe", "--stdio"]


def test_root_relative_solution_is_resolved_against_root(tmp_path):
    c = RoslynClient(str(tmp_path), solution="repo-a/A.sln")
    assert c.solution == str((tmp_path / "repo-a" / "A.sln").resolve())
    assert c.workspace_dir == str((tmp_path / "repo-a").resolve())


def test_log_dir_is_per_solution_stem(tmp_path):
    root = str(tmp_path)
    assert default_log_dir(root, None) == os.path.join(root, LOG_DIR_NAME)
    assert default_log_dir(root, os.path.join(root, "repo-b", "B.sln")) == \
        os.path.join(root, LOG_DIR_NAME, "B")
    c = RoslynClient(root, solution="repo-b/B.sln")
    assert c.log_dir == os.path.join(str(tmp_path.resolve()), LOG_DIR_NAME, "B")


def test_workspace_folders_request_answers_with_solution_dir(tmp_path):
    c = RoslynClient(str(tmp_path), solution="repo-b/B.sln")
    sent: list[dict] = []
    c._send = lambda m: sent.append(m)
    c._proc = type("P", (), {"poll": lambda self: None})()
    c._dispatch({"jsonrpc": "2.0", "id": 3, "method": "workspace/workspaceFolders", "params": {}})
    assert sent[-1]["result"] == [{"uri": path_to_uri(tmp_path / "repo-b"), "name": "repo-b"}]
