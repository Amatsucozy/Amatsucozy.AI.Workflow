"""Pure shaping helpers: LSP response shapes -> plain dicts for MCP tool
results. No I/O, no LSP client — kept separate from server.py so it can be
unit-tested without a running Roslyn process.
"""

from __future__ import annotations

import os

from roslyn_mcp.lsp_client import uri_to_path

SYMBOL_KINDS = {
    1: "file", 2: "module", 3: "namespace", 4: "package", 5: "class", 6: "method",
    7: "property", 8: "field", 9: "constructor", 10: "enum", 11: "interface",
    12: "function", 13: "variable", 14: "constant", 15: "string", 16: "number",
    17: "boolean", 18: "array", 19: "object", 20: "key", 21: "null",
    22: "enum_member", 23: "struct", 24: "event", 25: "operator", 26: "type_parameter",
}
SEVERITY = {1: "error", 2: "warning", 3: "info", 4: "hint"}


def rel(uri: str, root: str) -> str:
    p = uri_to_path(uri)
    try:
        return os.path.relpath(p, root).replace("\\", "/")
    except ValueError:
        return p


def loc(item: dict, root: str) -> dict:
    """Normalise Location | LocationLink to {file, line, col, end_line, end_col}."""
    uri = item.get("uri") or item.get("targetUri")
    rng = item.get("range") or item.get("targetSelectionRange") or item.get("targetRange") or {}
    s, e = rng.get("start", {}), rng.get("end", {})
    return {
        "file": rel(uri, root),
        "line": s.get("line", 0) + 1, "col": s.get("character", 0) + 1,
        "end_line": e.get("line", 0) + 1, "end_col": e.get("character", 0) + 1,
    }


def flatten_symbols(items: list[dict], root: str, container: str = "") -> list[dict]:
    out = []
    for it in items or []:
        if "location" in it:  # SymbolInformation (flat form)
            l = loc(it["location"], root)
            out.append({"name": it["name"], "kind": SYMBOL_KINDS.get(it.get("kind"), "?"),
                        "container": it.get("containerName", ""), **l})
        else:                 # DocumentSymbol (hierarchical)
            sel = it.get("selectionRange") or it.get("range") or {}
            s = sel.get("start", {})
            out.append({"name": it["name"], "kind": SYMBOL_KINDS.get(it.get("kind"), "?"),
                        "container": container, "detail": it.get("detail", ""),
                        "line": s.get("line", 0) + 1, "col": s.get("character", 0) + 1})
            out.extend(flatten_symbols(it.get("children", []), root,
                                       f"{container}.{it['name']}" if container else it["name"]))
    return out


def pos(line: int, col: int) -> dict:
    return {"line": max(line - 1, 0), "character": max(col - 1, 0)}
