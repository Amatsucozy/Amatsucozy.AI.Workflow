"""Tests for roslyn_mcp.workspaces — solution discovery, per-file resolution,
and the LRU client pool. No LSP, no subprocess: everything runs against
tmp_path trees and duck-typed fake clients."""

from __future__ import annotations

import os

import pytest

from roslyn_mcp.workspaces import ClientPool, discover_solutions, resolve_solution


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")
    return path


# ------------------------------------------------------------ discovery

def test_discover_finds_nested_solutions_sorted_and_relative(tmp_path):
    _touch(tmp_path / "repo-b" / "B.sln")
    _touch(tmp_path / "repo-a" / "A.sln")
    _touch(tmp_path / "repo-a" / "tools" / "Tools.slnx")
    assert discover_solutions(tmp_path) == ["repo-a/A.sln", "repo-a/tools/Tools.slnx", "repo-b/B.sln"]


def test_discover_skips_build_and_vcs_dirs(tmp_path):
    _touch(tmp_path / "A.sln")
    for d in ("bin", "obj", "node_modules", ".git"):
        _touch(tmp_path / d / "Hidden.sln")
    assert discover_solutions(tmp_path) == ["A.sln"]


def test_discover_respects_depth_bound(tmp_path):
    _touch(tmp_path / "a" / "b" / "c" / "d" / "Deep.sln")   # depth 4 dir
    _touch(tmp_path / "a" / "b" / "Shallow.sln")             # depth 2 dir
    assert discover_solutions(tmp_path, max_depth=3) == ["a/b/Shallow.sln"]
    assert discover_solutions(tmp_path, max_depth=4) == ["a/b/Shallow.sln", "a/b/c/d/Deep.sln"]


def test_discover_empty_root(tmp_path):
    assert discover_solutions(tmp_path) == []


# ------------------------------------------------------------ resolution

def test_resolve_single_solution_at_root(tmp_path):
    sln = _touch(tmp_path / "A.sln")
    f = _touch(tmp_path / "src" / "X.cs")
    r = resolve_solution(f, tmp_path)
    assert r.ok and r.reason == "ok"
    assert os.path.samefile(r.solution, sln)


def test_resolve_picks_nearest_directory(tmp_path):
    _touch(tmp_path / "Outer.sln")
    inner = _touch(tmp_path / "repo-b" / "B.sln")
    f = _touch(tmp_path / "repo-b" / "src" / "X.cs")
    r = resolve_solution(f, tmp_path)
    assert r.ok and os.path.samefile(r.solution, inner)


def test_resolve_multiple_in_same_dir_is_ambiguous_and_does_not_climb(tmp_path):
    _touch(tmp_path / "Outer.sln")  # unique, but farther away — must not win
    a = _touch(tmp_path / "repo" / "A.sln")
    b = _touch(tmp_path / "repo" / "B.slnx")
    f = _touch(tmp_path / "repo" / "src" / "X.cs")
    r = resolve_solution(f, tmp_path)
    assert not r.ok and r.reason == "multiple"
    assert [os.path.basename(c) for c in r.candidates] == [a.name, b.name]


def test_resolve_none_when_no_solution_up_to_root(tmp_path):
    _touch(tmp_path / "elsewhere" / "E.sln")
    f = _touch(tmp_path / "src" / "X.cs")
    r = resolve_solution(f, tmp_path)
    assert not r.ok and r.reason == "none" and r.candidates == []


def test_resolve_file_above_root_is_outside(tmp_path):
    root = tmp_path / "root"
    _touch(root / "A.sln")
    _touch(tmp_path / "A.sln")
    f = _touch(tmp_path / "X.cs")  # sibling of root, not inside it
    r = resolve_solution(f, root)
    assert not r.ok and r.reason == "outside_root" and r.candidates == []


# ------------------------------------------------------------ client pool

class FakeClient:
    def __init__(self, solution, fail_start=False):
        self.solution = solution
        self.alive = False
        self.started = 0
        self.shut = False
        self._fail = fail_start

    def start(self):
        if self._fail:
            raise FileNotFoundError("roslyn-language-server not found")
        self.alive = True
        self.started += 1

    def shutdown(self):
        self.alive = False
        self.shut = True


@pytest.fixture
def pool():
    made = []

    def factory(solution):
        c = FakeClient(solution)
        made.append(c)
        return c

    p = ClientPool(2, factory)
    p.made = made  # type: ignore[attr-defined]
    return p


def test_pool_starts_once_and_reuses(pool):
    a1 = pool.get("/r/A.sln")
    a2 = pool.get("/r/A.sln")
    assert a1 is a2 and a1.started == 1 and len(pool.made) == 1


def test_pool_evicts_least_recently_used_and_shuts_it_down(pool):
    a = pool.get("/r/A.sln")
    b = pool.get("/r/B.sln")
    pool.get("/r/A.sln")           # touch A: B is now the oldest
    c = pool.get("/r/C.sln")       # cap 2 -> B evicted
    assert b.shut and not a.shut and not c.shut
    assert [x.solution for x in pool.loaded()] == ["/r/A.sln", "/r/C.sln"]
    assert pool.peek("/r/B.sln") is None


def test_pool_replaces_dead_client(pool):
    a = pool.get("/r/A.sln")
    a.alive = False
    a2 = pool.get("/r/A.sln")
    assert a2 is not a and a2.alive and len(pool.loaded()) == 1


def test_pool_failed_start_is_not_cached(pool):
    pool._factory = lambda s: FakeClient(s, fail_start=True)
    with pytest.raises(FileNotFoundError):
        pool.get("/r/A.sln")
    assert pool.loaded() == [] and pool.peek("/r/A.sln") is None


def test_pool_none_key_is_the_autoload_client(pool):
    c = pool.get(None)
    assert c.solution is None and pool.peek(None) is c


def test_pool_most_recent_of_prefers_latest_alive_candidate(pool):
    a = pool.get("/r/A.sln")
    b = pool.get("/r/B.sln")
    assert pool.most_recent_of(["/r/A.sln", "/r/B.sln"]) is b
    pool.get("/r/A.sln")
    assert pool.most_recent_of(["/r/A.sln", "/r/B.sln"]) is a
    a.alive = False
    assert pool.most_recent_of(["/r/A.sln", "/r/B.sln"]) is b
    assert pool.most_recent_of(["/r/Z.sln"]) is None


def test_pool_min_size_is_one():
    p = ClientPool(0, FakeClient)
    assert p.max_size == 1
    p.get("/r/A.sln")
    p.get("/r/B.sln")
    assert [c.solution for c in p.loaded()] == ["/r/B.sln"]
