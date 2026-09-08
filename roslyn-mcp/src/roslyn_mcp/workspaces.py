"""Solution discovery, per-file solution resolution, and the per-solution
client pool.

Pure logic — no LSP traffic, no subprocesses — kept apart from server.py and
lsp_client.py so it can be unit-tested with fakes.

Why this exists: a server root that holds several repositories holds several
`.sln` files. Letting Roslyn auto-discover from the root either loads the
wrong one or never finishes loading. Instead we map each requested file to
the nearest directory (walking up towards the root) that contains exactly
one solution, and keep one Roslyn process per solution.
"""

from __future__ import annotations

import os
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Optional

SOLUTION_SUFFIXES = (".sln", ".slnx")
#: Directory names never descended into during discovery (case-insensitive).
SKIP_DIRS = frozenset({"bin", "obj", "node_modules", ".git", ".vs", ".roslyn-mcp"})
#: Discovery depth bound: root itself is depth 0, `repo-a/` is depth 1.
DEFAULT_MAX_DEPTH = 4


def norm_key(path: str | os.PathLike) -> str:
    """Canonical dictionary key for a path (case-folded on Windows)."""
    return os.path.normcase(os.path.realpath(str(path)))


def _solutions_in(directory: str) -> list[str]:
    """Absolute paths of the solution files directly inside `directory`."""
    try:
        names = os.listdir(directory)
    except OSError:
        return []
    out = []
    for n in sorted(names):
        p = os.path.join(directory, n)
        if n.lower().endswith(SOLUTION_SUFFIXES) and os.path.isfile(p):
            out.append(p)
    return out


def discover_solutions(root: str | os.PathLike, max_depth: int = DEFAULT_MAX_DEPTH) -> list[str]:
    """Relative (forward-slash) paths of every `.sln`/`.slnx` under `root`,
    at most `max_depth` directories deep, skipping SKIP_DIRS. Sorted."""
    root = os.path.realpath(str(root))
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else len(rel.replace("\\", "/").split("/"))
        if depth >= max_depth:
            dirnames[:] = []
        else:
            dirnames[:] = sorted(d for d in dirnames if d.lower() not in SKIP_DIRS)
        for f in sorted(filenames):
            if f.lower().endswith(SOLUTION_SUFFIXES):
                found.append(os.path.relpath(os.path.join(dirpath, f), root).replace("\\", "/"))
    return sorted(found)


@dataclass
class Resolution:
    """Outcome of resolve_solution().

    reason:
      ok            - exactly one solution found in the nearest owning dir
      multiple      - the nearest dir holding any solution holds several
      none          - no solution between the file's dir and the root
      outside_root  - the file is not under the root at all
    """
    solution: Optional[str]
    candidates: list[str]
    reason: str

    @property
    def ok(self) -> bool:
        return self.solution is not None


def resolve_solution(file: str | os.PathLike, root: str | os.PathLike) -> Resolution:
    """Walk up from `file`'s directory to `root` and pick the nearest directory
    containing exactly one solution file. Stops (ambiguous) at the first
    directory holding more than one — a closer ambiguity is never skipped in
    favour of a farther unique solution."""
    root_r = os.path.realpath(str(root))
    d = os.path.dirname(os.path.realpath(str(file)))
    try:
        inside = os.path.normcase(os.path.commonpath([root_r, d])) == os.path.normcase(root_r)
    except ValueError:  # different drives on Windows
        inside = False
    if not inside:
        return Resolution(None, [], "outside_root")
    while True:
        slns = _solutions_in(d)
        if len(slns) == 1:
            return Resolution(slns[0], slns, "ok")
        if len(slns) > 1:
            return Resolution(None, slns, "multiple")
        if os.path.normcase(d) == os.path.normcase(root_r):
            break
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return Resolution(None, [], "none")


class ClientPool:
    """LRU cache of started clients keyed by solution path (None = the
    auto-load fallback client that has no explicit solution).

    `factory(solution)` builds an unstarted client; the pool calls `start()`
    on it. A client that fails to start is never cached, and a cached client
    found dead is dropped before its replacement is built — so a failed
    restart can never leave a dead instance serving (fail closed).
    Evicted clients get `shutdown()`.
    """

    def __init__(self, max_size: int, factory: Callable[[Optional[str]], Any]):
        self.max_size = max(1, int(max_size))
        self._factory = factory
        self._items: "OrderedDict[Optional[str], Any]" = OrderedDict()

    @staticmethod
    def key(solution: Optional[str]) -> Optional[str]:
        return None if solution is None else norm_key(solution)

    def get(self, solution: Optional[str]) -> Any:
        """Return the live client for `solution`, starting or restarting it."""
        k = self.key(solution)
        c = self._items.get(k)
        if c is not None and c.alive:
            self._items.move_to_end(k)
            return c
        if c is not None:
            self._items.pop(k, None)
        c = self._factory(solution)
        c.start()
        self._items[k] = c
        while len(self._items) > self.max_size:
            _, old = self._items.popitem(last=False)
            try:
                old.shutdown()
            except Exception:
                pass
        return c

    def peek(self, solution: Optional[str]) -> Any:
        """Cached client (alive or not) without starting or touching LRU order."""
        return self._items.get(self.key(solution))

    def loaded(self) -> list[Any]:
        """All cached clients, least recently used first."""
        return list(self._items.values())

    def most_recent(self) -> Any:
        return next(reversed(self._items.values())) if self._items else None

    def most_recent_of(self, solutions: list[str]) -> Any:
        """The most recently used cached *alive* client whose solution is in
        `solutions`, or None."""
        wanted = {self.key(s) for s in solutions}
        for k, c in reversed(self._items.items()):
            if k in wanted and c.alive:
                return c
        return None

    def shutdown_all(self) -> None:
        while self._items:
            _, c = self._items.popitem(last=False)
            try:
                c.shutdown()
            except Exception:
                pass
