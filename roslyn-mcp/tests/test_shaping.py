import json, threading
from roslyn_mcp import server, shaping
from roslyn_mcp.lsp_client import path_to_uri, uri_to_path, RoslynClient


def test_uri_roundtrip(tmp_path):
    f = tmp_path / "A.cs"
    f.write_text("class A {}")
    assert uri_to_path(path_to_uri(f)) == str(f.resolve())


def test_loc_handles_location_and_locationlink():
    root = "/repo"
    loc = {"uri": "file:///repo/src/A.cs", "range": {"start": {"line": 4, "character": 2},
                                                     "end": {"line": 4, "character": 7}}}
    link = {"targetUri": "file:///repo/src/B.cs",
            "targetSelectionRange": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}}}
    assert shaping.loc(loc, root) == {"file": "src/A.cs", "line": 5, "col": 3, "end_line": 5, "end_col": 8}
    assert shaping.loc(link, root)["file"] == "src/B.cs"


def test_flatten_document_symbols():
    syms = [{"name": "Foo", "kind": 5, "selectionRange": {"start": {"line": 1, "character": 6}},
             "children": [{"name": "Bar", "kind": 6, "selectionRange": {"start": {"line": 3, "character": 12}}}]}]
    out = shaping.flatten_symbols(syms, "/repo")
    assert [(s["name"], s["kind"], s["container"], s["line"]) for s in out] == \
        [("Foo", "class", "", 2), ("Bar", "method", "Foo", 4)]


def test_dispatch_answers_server_requests_and_gates_ready():
    c = RoslynClient("/tmp")
    sent = []
    c._send = lambda m: sent.append(m)
    c._proc = type("P", (), {"poll": lambda self: None})()
    c._dispatch({"jsonrpc": "2.0", "id": 7, "method": "workspace/configuration",
                 "params": {"items": [{}, {}]}})
    assert sent[-1] == {"jsonrpc": "2.0", "id": 7, "result": [None, None]}
    assert not c._ready.is_set()
    c._dispatch({"jsonrpc": "2.0", "method": "workspace/projectInitializationComplete"})
    assert c._ready.is_set()


def test_tools_registered():
    import asyncio
    names = sorted(t.name for t in asyncio.run(server.mcp.list_tools()))
    assert names == ["definition", "diagnostics", "document_symbols", "hover", "implementations",
                     "references", "refresh_file", "rename_preview", "workspace_status"]
