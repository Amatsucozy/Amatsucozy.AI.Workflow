"""roslyn-mcp: structured C# semantic tools over roslyn-language-server.

Every tool returns a dict with a `verdict` field:
  ok                  - query ran against a fully loaded workspace
  workspace_loading   - Roslyn has not finished loading projects; results
                        (if any) are unreliable, retry after workspace_status
                        reports ready
  file_not_found      - the path does not exist on disk
  server_error        - Roslyn returned an LSP error (see `error`)
  server_dead         - Roslyn process exited; call workspace_status to restart
  timeout             - request exceeded its deadline

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

mcp = MCPServer("roslyn-mcp")

_client: Optional[RoslynClient] = None
_client_lock = threading.Lock()


def _root() -> str:
    return os.environ.get("ROSLYN_MCP_ROOT") or os.getcwd()


def _get() -> RoslynClient:
    global _client
    with _client_lock:
        if _client is None or not _client.alive:
            _client = RoslynClient(_root())
            _client.start()
        return _client


def _run(fn, *, needs_ready: bool = True) -> dict:
    """Common wrapper: readiness gate + error → verdict mapping."""
    try:
        c = _get()
        if needs_ready and not c.ready:
            c.wait_ready(timeout=float(os.environ.get("ROSLYN_TOOL_READY_WAIT", "30")))
        verdict = "ok" if c.ready else "workspace_loading"
        result = fn(c)
        result.setdefault("verdict", verdict)
        if verdict != "ok":
            result["verdict"] = "workspace_loading"
            result["hint"] = ("Roslyn is still loading projects; results above may be empty "
                              "or partial. Poll workspace_status until ready=true.")
        return result
    except FileNotFoundError as e:
        return {"verdict": "file_not_found", "error": str(e)}
    except LspError as e:
        return {"verdict": "server_error", "error": e.message, "code": e.code, "data": e.data}
    except LspDead as e:
        return {"verdict": "server_dead", "error": str(e)}
    except TimeoutError as e:
        return {"verdict": "timeout", "error": str(e)}


def _check_file(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = Path(_root()) / p
    if not p.is_file():
        raise FileNotFoundError(f"{p} does not exist")
    return str(p.resolve())


# -------------------------------------------------------------------- tools

@mcp.tool()
def workspace_status(wait_seconds: float = 0) -> dict:
    """Report whether roslyn-language-server is running and has finished loading
    the solution/projects under the server's root (cwd, or ROSLYN_MCP_ROOT).

    Starts the server if it is not running. Set `wait_seconds` > 0 to block up
    to that long for project load to complete (typically 20-120 s on first
    start; the server stays warm afterwards).

    Returns: alive, ready, uptime_seconds, root, and `verdict`
    ("ok" when ready, "workspace_loading" otherwise, "server_dead" on crash).
    Call this first, and re-check it whenever another tool returns
    workspace_loading.
    """
    try:
        c = _get()
        if wait_seconds > 0 and not c.ready:
            c.wait_ready(timeout=min(wait_seconds, DEFAULT_READY_TIMEOUT))
        v = "ok" if c.ready else ("workspace_loading" if c.alive else "server_dead")
        return {"verdict": v, "alive": c.alive, "ready": c.ready,
                "uptime_seconds": round(c.uptime(), 1), "root": c.root,
                "log_dir": c.log_dir, "exit_code": c.exit_code}
    except FileNotFoundError as e:
        return {"verdict": "server_dead", "alive": False, "ready": False, "error": str(e)}


@mcp.tool()
def document_symbols(file: str) -> dict:
    """List every declared symbol in a C# file (namespaces, types, members),
    flattened with a dotted `container` and 1-based `line`/`col` of each name.

    `file` is absolute or relative to the server root. Use this to find the
    exact position to pass to definition/references/hover/rename.
    """
    path = _check_file(file)

    def go(c: RoslynClient) -> dict:
        uri = c.open(path)
        res = c.request("textDocument/documentSymbol", {"textDocument": {"uri": uri}})
        syms = flatten_symbols(res or [], c.root)
        return {"file": _rel(uri, c.root), "count": len(syms), "symbols": syms}
    return _run(go)


@mcp.tool()
def definition(file: str, line: int, col: int) -> dict:
    """Go to definition of the symbol at (line, col) (1-based). Returns
    `locations` [{file, line, col, ...}]. Empty list with verdict ok means the
    position is not on a resolvable symbol (or it is metadata-only, e.g. BCL).
    """
    path = _check_file(file)

    def go(c: RoslynClient) -> dict:
        uri = c.open(path)
        res = c.request("textDocument/definition",
                        {"textDocument": {"uri": uri}, "position": _pos(line, col)})
        items = res if isinstance(res, list) else ([res] if res else [])
        return {"locations": [_loc(i, c.root) for i in items]}
    return _run(go)


@mcp.tool()
def implementations(file: str, line: int, col: int) -> dict:
    """Find implementations of the interface/abstract/virtual member or type at
    (line, col). Returns `locations` like `definition`."""
    path = _check_file(file)

    def go(c: RoslynClient) -> dict:
        uri = c.open(path)
        res = c.request("textDocument/implementation",
                        {"textDocument": {"uri": uri}, "position": _pos(line, col)})
        items = res if isinstance(res, list) else ([res] if res else [])
        return {"locations": [_loc(i, c.root) for i in items]}
    return _run(go)


@mcp.tool()
def references(file: str, line: int, col: int, include_declaration: bool = True,
               max_results: int = 200) -> dict:
    """Find all references to the symbol at (line, col) across the loaded
    solution. Returns `total`, `truncated`, and `by_file`: {relative_path:
    [{line, col}, ...]} sorted by file. A `total` of 0 with verdict ok is a
    real answer; with verdict workspace_loading it is NOT — retry later.
    """
    path = _check_file(file)

    def go(c: RoslynClient) -> dict:
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
    return _run(go)


@mcp.tool()
def hover(file: str, line: int, col: int) -> dict:
    """Return the signature/documentation Roslyn shows on hover for the symbol
    at (line, col), as `text` (markdown). Cheapest way to get a resolved type
    or full method signature without opening the definition."""
    path = _check_file(file)

    def go(c: RoslynClient) -> dict:
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
    return _run(go)


@mcp.tool()
def diagnostics(file: str, min_severity: str = "warning") -> dict:
    """Pull compiler + analyzer diagnostics for one file from the live Roslyn
    workspace (no `dotnet build` needed; reflects unsaved-to-build state on
    disk). `min_severity`: error | warning | info | hint. Returns `errors`,
    `warnings`, and `items` [{severity, code, line, col, message}].

    For a whole-solution gate still use amtcz `sarif_build`; this is for
    fast per-file checks after an edit.
    """
    path = _check_file(file)
    order = {"error": 1, "warning": 2, "info": 3, "hint": 4}
    cutoff = order.get(min_severity, 2)

    def go(c: RoslynClient) -> dict:
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
    return _run(go)


@mcp.tool()
def rename_preview(file: str, line: int, col: int, new_name: str) -> dict:
    """Compute a solution-wide rename of the symbol at (line, col) WITHOUT
    applying it. Returns `by_file`: {relative_path: [{line, col, end_line,
    end_col, new_text}]} so the agent can review or apply the edits itself.
    Nothing on disk is modified by this tool.
    """
    path = _check_file(file)

    def go(c: RoslynClient) -> dict:
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
    return _run(go)


@mcp.tool()
def refresh_file(file: str) -> dict:
    """Tell Roslyn a file changed on disk (after the agent edits it) so later
    queries see the new content. Also closes nothing — documents stay open
    for the server's lifetime. Returns verdict ok."""
    path = _check_file(file)

    def go(c: RoslynClient) -> dict:
        c.refresh(path)
        return {"file": _rel(c.open(path), c.root)}
    return _run(go, needs_ready=False)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
