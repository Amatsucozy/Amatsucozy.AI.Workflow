"""roslyn-mcp: structured C# semantic tools over roslyn-language-server.

Every tool returns a dict with a `verdict` field:
  ok                   - query ran against a fully loaded workspace
  workspace_loading    - Roslyn has not finished loading projects; results
                         (if any) are unreliable, retry after workspace_status
                         reports ready
  workspace_unselected - the file could not be mapped to exactly one solution
                         (several .sln/.slnx own it, or none does but the root
                         holds some); pick one from `candidates` with
                         workspace_status(solution=...) then repeat the call
  file_not_found       - the path does not exist on disk
  server_error         - Roslyn returned an LSP error (see `error`)
  server_dead          - Roslyn process exited or could not be launched; call
                         workspace_status to restart
  timeout              - request exceeded its deadline

Solution selection (multi-repo roots): each file is mapped to the nearest
directory, walking up to the root, that contains exactly one solution file.
One Roslyn process is kept per solution (LRU, ROSLYN_MCP_MAX_WORKSPACES).
ROSLYN_MCP_SOLUTION forces a single solution and skips discovery. A root
with no solution at all falls back to Roslyn's --autoLoadProjects.

All line/column values in inputs and outputs are 1-based.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any, Optional

try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer  # type: ignore

from roslyn_mcp.lsp_client import (
    DEFAULT_READY_TIMEOUT, LspDead, LspError, RoslynClient,
)
from roslyn_mcp.shaping import SEVERITY, flatten_symbols, loc as _loc, pos as _pos, rel as _rel
from roslyn_mcp.workspaces import ClientPool, discover_solutions, resolve_solution

mcp = MCPServer("roslyn-mcp")

DEFAULT_MAX_WORKSPACES = 2
UNSELECTED_HINT = ("More than one solution could own this file. Call "
                   "workspace_status(solution=<one of candidates>) to load it, then "
                   "repeat this same call. Set ROSLYN_MCP_SOLUTION to pin one for good.")


def _root() -> str:
    # realpath: solution/file paths are canonicalised (8.3 short names, symlinks,
    # case) before being made root-relative, so the root must be too.
    return os.path.realpath(os.environ.get("ROSLYN_MCP_ROOT") or os.getcwd())


def _forced_solution() -> Optional[str]:
    """ROSLYN_MCP_SOLUTION: absolute or root-relative path that pins the one
    solution every tool uses. Discovery is skipped entirely when set."""
    s = os.environ.get("ROSLYN_MCP_SOLUTION")
    if not s:
        return None
    p = Path(s)
    return str(p if p.is_absolute() else Path(_root()) / p)


def _max_workspaces() -> int:
    try:
        return int(os.environ.get("ROSLYN_MCP_MAX_WORKSPACES", "") or DEFAULT_MAX_WORKSPACES)
    except ValueError:
        return DEFAULT_MAX_WORKSPACES


def _make_client(solution: Optional[str]) -> RoslynClient:
    return RoslynClient(_root(), solution=solution)


def _new_pool() -> ClientPool:
    return ClientPool(_max_workspaces(), _make_client)


_pool: ClientPool = _new_pool()
_pool_lock = threading.Lock()


class _Unselected(Exception):
    def __init__(self, candidates: list[str]):
        super().__init__("workspace_unselected")
        self.candidates = candidates


def _rel_root(path: Optional[str]) -> Optional[str]:
    if path is None:
        return None
    try:
        return os.path.relpath(path, _root()).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def _unselected(candidates: list[str]) -> dict:
    return {"verdict": "workspace_unselected",
            "candidates": [_rel_root(c) for c in candidates], "hint": UNSELECTED_HINT}


def _select_solution(path: str) -> Optional[str]:
    """Map an absolute file path to the solution its Roslyn process should
    load (None = auto-load fallback). Raises _Unselected when ambiguous.
    Caller holds _pool_lock."""
    forced = _forced_solution()
    if forced:
        return forced
    root = _root()
    r = resolve_solution(path, root)
    if r.ok:
        return r.solution
    if r.reason == "multiple":
        candidates = r.candidates
    else:  # none / outside_root: offer everything the root holds
        candidates = [os.path.join(root, s) for s in discover_solutions(root)]
        if not candidates:
            return None  # single-repo without a .sln: legacy --autoLoadProjects
    picked = _pool.most_recent_of(candidates)  # the agent already chose one
    if picked is not None:
        return picked.solution
    raise _Unselected(candidates)


def _run(fn, file: str, *, needs_ready: bool = True) -> dict:
    """Common wrapper: file check, solution resolution, readiness gate, and
    error -> verdict mapping. `fn(client, abs_path)` does the LSP work."""
    try:
        path = _check_file(file)
    except FileNotFoundError as e:
        return {"verdict": "file_not_found", "error": str(e)}
    try:
        with _pool_lock:
            c = _pool.get(_select_solution(path))
    except _Unselected as e:
        return _unselected(e.candidates)
    except FileNotFoundError as e:  # roslyn-language-server not launchable
        return {"verdict": "server_dead", "error": str(e)}
    try:
        if needs_ready and not c.ready:
            c.wait_ready(timeout=float(os.environ.get("ROSLYN_TOOL_READY_WAIT", "30")))
        verdict = "ok" if c.ready else "workspace_loading"
        result = fn(c, path)
        # verdict/solution/hint lead the dict so they survive clients that
        # truncate long payloads (a 168-symbol list would otherwise bury them).
        head: dict[str, Any] = {"verdict": result.pop("verdict", verdict),
                                "solution": _rel_root(c.solution)}
        if verdict != "ok":
            head["verdict"] = "workspace_loading"
            head["hint"] = ("Roslyn is still loading projects; results below may be empty "
                            "or partial. Poll workspace_status until ready=true.")
        return {**head, **result}
    except FileNotFoundError as e:
        return {"verdict": "file_not_found", "error": str(e)}
    except LspError as e:
        return {"verdict": "server_error", "error": e.message, "code": e.code, "data": e.data}
    except LspDead as e:
        return {"verdict": "server_dead", "error": str(e), "solution": _rel_root(c.solution)}
    except TimeoutError as e:
        return {"verdict": "timeout", "error": str(e), "solution": _rel_root(c.solution)}


def _check_file(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = Path(_root()) / p
    if not p.is_file():
        raise FileNotFoundError(f"{p} does not exist")
    return str(p.resolve())


def _ws_info(c: RoslynClient) -> dict:
    return {"solution": _rel_root(c.solution), "alive": c.alive, "ready": c.ready,
            "uptime_seconds": round(c.uptime(), 1), "log_dir": c.log_dir, "exit_code": c.exit_code}


# -------------------------------------------------------------------- tools

@mcp.tool()
def workspace_status(wait_seconds: float = 0, solution: Optional[str] = None) -> dict:
    """Report which solutions the server root holds, which Roslyn workspaces
    are loaded, and whether the current one has finished loading projects.
    Starts (or restarts) a Roslyn process when needed.

    `solution`: root-relative or absolute .sln/.slnx to load and make current.
    Use it after any tool answered `workspace_unselected`, picking one of its
    `candidates`; then repeat that tool call. Without it the server picks the
    already-loaded workspace, else the root's single solution, else answers
    `workspace_unselected` with `candidates` when the root holds several.
    `wait_seconds` > 0 blocks up to that long for project load (typically
    20-120 s on first start; the process stays warm afterwards).

    Returns: verdict, root, solutions (all discovered, or just the pinned
    ROSLYN_MCP_SOLUTION), workspaces (every loaded process with alive/ready/
    log_dir), plus alive/ready/uptime_seconds/solution/log_dir of the current
    one. verdict: "ok" when ready, "workspace_loading" while loading,
    "workspace_unselected" when a choice is needed, "server_dead" on crash or
    launch failure, "file_not_found" when `solution` does not exist.
    """
    root = _root()
    forced = _forced_solution()
    base: dict[str, Any] = {"root": root, "max_workspaces": _pool.max_size}
    try:
        use_recent = False
        if forced:
            target: Optional[str] = forced
            base["solutions"] = [_rel_root(forced)]
            base["pinned"] = True
        else:
            found = discover_solutions(root)
            base["solutions"] = found
            if solution:
                p = Path(solution)
                if not p.is_absolute():
                    p = Path(root) / p
                if not p.is_file():
                    return {"verdict": "file_not_found", "error": f"{p} does not exist", **base}
                target = str(p)
            elif _pool.loaded():
                use_recent, target = True, None
            elif len(found) == 1:
                target = os.path.join(root, found[0])
            elif not found:
                target = None  # no .sln anywhere: legacy --autoLoadProjects
            else:
                return {"verdict": "workspace_unselected", "candidates": found,
                        "hint": UNSELECTED_HINT, "workspaces": [], **base}
        with _pool_lock:
            c = _pool.most_recent() if use_recent else _pool.get(target)
            if not c.alive:  # most recent died: restart it in place
                c = _pool.get(c.solution)
        if wait_seconds > 0 and not c.ready:
            c.wait_ready(timeout=min(wait_seconds, DEFAULT_READY_TIMEOUT))
        v = "ok" if c.ready else ("workspace_loading" if c.alive else "server_dead")
        return {"verdict": v, **_ws_info(c), "workspaces": [_ws_info(x) for x in _pool.loaded()], **base}
    except FileNotFoundError as e:
        return {"verdict": "server_dead", "alive": False, "ready": False, "error": str(e), **base}


@mcp.tool()
def document_symbols(file: str) -> dict:
    """List every declared symbol in a C# file (namespaces, types, members),
    flattened with a dotted `container` and 1-based `line`/`col` of each name.

    `file` is absolute or relative to the server root. Use this to find the
    exact position to pass to definition/references/hover/rename. The owning
    solution is resolved from the file's location automatically; every
    result reports it as `solution`.
    """
    def go(c: RoslynClient, path: str) -> dict:
        uri = c.open(path)
        res = c.request("textDocument/documentSymbol", {"textDocument": {"uri": uri}})
        syms = flatten_symbols(res or [], c.root)
        return {"file": _rel(uri, c.root), "count": len(syms), "symbols": syms}
    return _run(go, file)


@mcp.tool()
def definition(file: str, line: int, col: int) -> dict:
    """Go to definition of the symbol at (line, col) (1-based). Returns
    `locations` [{file, line, col, ...}]. Empty list with verdict ok means the
    position is not on a resolvable symbol (or it is metadata-only, e.g. BCL).
    """
    def go(c: RoslynClient, path: str) -> dict:
        uri = c.open(path)
        res = c.request("textDocument/definition",
                        {"textDocument": {"uri": uri}, "position": _pos(line, col)})
        items = res if isinstance(res, list) else ([res] if res else [])
        return {"locations": [_loc(i, c.root) for i in items]}
    return _run(go, file)


@mcp.tool()
def implementations(file: str, line: int, col: int) -> dict:
    """Find implementations of the interface/abstract/virtual member or type at
    (line, col). Returns `locations` like `definition`."""
    def go(c: RoslynClient, path: str) -> dict:
        uri = c.open(path)
        res = c.request("textDocument/implementation",
                        {"textDocument": {"uri": uri}, "position": _pos(line, col)})
        items = res if isinstance(res, list) else ([res] if res else [])
        return {"locations": [_loc(i, c.root) for i in items]}
    return _run(go, file)


@mcp.tool()
def references(file: str, line: int, col: int, include_declaration: bool = True,
               max_results: int = 200) -> dict:
    """Find all references to the symbol at (line, col) across the file's
    solution (never across solutions). Returns `total`, `truncated`, and `by_file`: {relative_path:
    [{line, col}, ...]} sorted by file. A `total` of 0 with verdict ok is a
    real answer; with verdict workspace_loading it is NOT — retry later.
    """
    def go(c: RoslynClient, path: str) -> dict:
        uri = c.open(path)
        res = c.request("textDocument/references", {
            "textDocument": {"uri": uri}, "position": _pos(line, col),
            "context": {"includeDeclaration": include_declaration},
        }, timeout=120) or []
        locs = sorted((_loc(i, c.root) for i in res), key=lambda l: (l["file"], l["line"], l["col"]))
        by_file: dict[str, list] = {}
        for l in locs[:max_results]:
            by_file.setdefault(l["file"], []).append({"line": l["line"], "col": l["col"]})
        return {"total": len(locs), "truncated": len(locs) > max_results,
                "files": len(by_file), "by_file": by_file}
    return _run(go, file)


@mcp.tool()
def hover(file: str, line: int, col: int) -> dict:
    """Return the signature/documentation Roslyn shows on hover for the symbol
    at (line, col), as `text` (markdown). Cheapest way to get a resolved type
    or full method signature without opening the definition."""
    def go(c: RoslynClient, path: str) -> dict:
        uri = c.open(path)
        res = c.request("textDocument/hover",
                        {"textDocument": {"uri": uri}, "position": _pos(line, col)})
        if not res:
            return {"text": ""}
        contents = res.get("contents")
        if isinstance(contents, dict):
            text = contents.get("value", "")
        elif isinstance(contents, list):
            text = "\n".join(x.get("value", x) if isinstance(x, dict) else str(x) for x in contents)
        else:
            text = str(contents or "")
        return {"text": text}
    return _run(go, file)


@mcp.tool()
def diagnostics(file: str, min_severity: str = "warning") -> dict:
    """Pull compiler + analyzer diagnostics for one file from the live Roslyn
    workspace (no `dotnet build` needed; reflects unsaved-to-build state on
    disk). `min_severity`: error | warning | info | hint. Returns `errors`,
    `warnings`, and `items` [{severity, code, line, col, message}].

    For a whole-solution gate still use amtcz `sarif_build`; this is for
    fast per-file checks after an edit.
    """
    order = {"error": 1, "warning": 2, "info": 3, "hint": 4}
    cutoff = order.get(min_severity, 2)

    def go(c: RoslynClient, path: str) -> dict:
        uri = c.refresh(path)  # re-sync from disk: agent probably just edited it
        res = c.request("textDocument/diagnostic", {"textDocument": {"uri": uri}}, timeout=90)
        raw = (res or {}).get("items", []) if isinstance(res, dict) else []
        items = []
        for d in raw:
            sev = d.get("severity", 2)
            if sev > cutoff:
                continue
            s = d.get("range", {}).get("start", {})
            items.append({"severity": SEVERITY.get(sev, "?"), "code": str(d.get("code", "")),
                          "line": s.get("line", 0) + 1, "col": s.get("character", 0) + 1,
                          "message": " ".join((d.get("message") or "").split())})
        items.sort(key=lambda x: (order.get(x["severity"], 9), x["line"]))
        return {"file": _rel(uri, c.root),
                "errors": sum(1 for i in items if i["severity"] == "error"),
                "warnings": sum(1 for i in items if i["severity"] == "warning"),
                "items": items}
    return _run(go, file)


@mcp.tool()
def rename_preview(file: str, line: int, col: int, new_name: str) -> dict:
    """Compute a solution-wide rename of the symbol at (line, col) WITHOUT
    applying it. Returns `by_file`: {relative_path: [{line, col, end_line,
    end_col, new_text}]} so the agent can review or apply the edits itself.
    Nothing on disk is modified by this tool.
    """
    def go(c: RoslynClient, path: str) -> dict:
        uri = c.open(path)
        res = c.request("textDocument/rename", {
            "textDocument": {"uri": uri}, "position": _pos(line, col), "newName": new_name,
        }, timeout=120) or {}
        by_file: dict[str, list] = {}

        def add(u: str, edits: list):
            for e in edits:
                r = e.get("range", {})
                s, en = r.get("start", {}), r.get("end", {})
                by_file.setdefault(_rel(u, c.root), []).append({
                    "line": s.get("line", 0) + 1, "col": s.get("character", 0) + 1,
                    "end_line": en.get("line", 0) + 1, "end_col": en.get("character", 0) + 1,
                    "new_text": e.get("newText", "")})

        for u, edits in (res.get("changes") or {}).items():
            add(u, edits)
        for dc in res.get("documentChanges") or []:
            if "textDocument" in dc:
                add(dc["textDocument"]["uri"], dc.get("edits", []))
        total = sum(len(v) for v in by_file.values())
        return {"new_name": new_name, "files": len(by_file), "edits": total, "by_file": by_file}
    return _run(go, file)


@mcp.tool()
def refresh_file(file: str) -> dict:
    """Tell Roslyn a file changed on disk (after the agent edits it) so later
    queries see the new content. Also closes nothing — documents stay open
    for the server's lifetime. Returns verdict ok."""
    def go(c: RoslynClient, path: str) -> dict:
        c.refresh(path)
        return {"file": _rel(c.open(path), c.root)}
    return _run(go, file, needs_ready=False)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
