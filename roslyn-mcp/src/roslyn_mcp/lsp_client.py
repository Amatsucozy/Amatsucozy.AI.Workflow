"""Minimal LSP client for roslyn-language-server over stdio.

Design notes
- One long-lived Roslyn process per MCP server process. Spawned lazily on
  first use, kept warm so repeated tool calls don't pay the project-load cost.
- A reader thread owns Roslyn's stdout. Responses are matched by id;
  notifications and server->client requests are dispatched by method.
- Roslyn sends `workspace/projectInitializationComplete` once
  --autoLoadProjects finishes. Semantic queries before that return empty
  results that look like "no hits" — so we gate on it (see wait_ready()).
- Nothing here ever writes to *our own* stdout: that pipe belongs to MCP.
  Roslyn's stderr goes to a log file, never to our stdio.
"""

from __future__ import annotations

import itertools
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import unquote, urlparse
from urllib.request import pathname2url

PROJECT_INIT_COMPLETE = "workspace/projectInitializationComplete"
DEFAULT_CMD = os.environ.get("ROSLYN_LSP_CMD", "roslyn-language-server")
DEFAULT_READY_TIMEOUT = float(os.environ.get("ROSLYN_READY_TIMEOUT", "180"))
DEFAULT_REQUEST_TIMEOUT = float(os.environ.get("ROSLYN_REQUEST_TIMEOUT", "60"))


class LspError(RuntimeError):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(f"LSP error {code}: {message}")
        self.code, self.message, self.data = code, message, data


class LspDead(RuntimeError):
    """Roslyn process exited or its pipe closed."""


# ---------------------------------------------------------------- uri helpers

def path_to_uri(path: str | os.PathLike) -> str:
    p = Path(path).resolve()
    return "file:" + pathname2url(str(p))  # yields file:///C:/... on Windows


def uri_to_path(uri: str) -> str:
    if not uri.startswith("file:"):
        return uri
    p = unquote(urlparse(uri).path)
    if len(p) > 2 and p[0] == "/" and p[2] == ":":  # /C:/x -> C:/x
        p = p[1:]
    return str(Path(p))


# ------------------------------------------------------------------- client

class RoslynClient:
    def __init__(
        self,
        root: str,
        cmd: str = DEFAULT_CMD,
        extra_args: Optional[list[str]] = None,
        log_dir: Optional[str] = None,
    ):
        self.root = str(Path(root).resolve())
        self.cmd = cmd
        self.extra_args = extra_args or []
        self.log_dir = log_dir or os.path.join(self.root, ".roslyn-mcp")
        self._proc: Optional[subprocess.Popen] = None
        self._ids = itertools.count(1)
        self._pending: dict[int, tuple[threading.Event, dict]] = {}
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._ready = threading.Event()
        self._dead = threading.Event()
        self._started_at: Optional[float] = None
        self._open_docs: dict[str, int] = {}  # uri -> version
        self.notifications: list[dict] = []   # last N, for debugging
        self.server_capabilities: dict = {}
        self.exit_code: Optional[int] = None
        self._handlers: dict[str, Callable[[dict], Any]] = {
            "client/registerCapability": lambda p: None,
            "client/unregisterCapability": lambda p: None,
            "window/workDoneProgress/create": lambda p: None,
            "workspace/configuration": lambda p: [None] * len(p.get("items", [])),
            "workspace/workspaceFolders": lambda p: [
                {"uri": path_to_uri(self.root), "name": Path(self.root).name}
            ],
            "window/showMessageRequest": lambda p: None,
            "workspace/applyEdit": lambda p: {"applied": False},
        }

    # ------------------------------------------------------------ lifecycle
    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None and not self._dead.is_set()

    @property
    def ready(self) -> bool:
        return self.alive and self._ready.is_set()

    def uptime(self) -> float:
        return time.time() - self._started_at if self._started_at else 0.0

    def start(self) -> None:
        if self.alive:
            return
        exe = shutil.which(self.cmd) or self.cmd
        if not (os.path.isabs(exe) and os.path.exists(exe)) and shutil.which(self.cmd) is None:
            raise FileNotFoundError(
                f"'{self.cmd}' not found on PATH. Install with "
                "`dotnet tool install --global roslyn-language-server --prerelease` "
                "or set ROSLYN_LSP_CMD to the full path of roslyn-language-server(.cmd)."
            )
        os.makedirs(self.log_dir, exist_ok=True)
        stderr = open(os.path.join(self.log_dir, "roslyn-stderr.log"), "ab")
        args = [exe, "--stdio", "--autoLoadProjects", "--logLevel", "Warning",
                "--extensionLogDirectory", self.log_dir, *self.extra_args]
        # On Windows, a .cmd wrapper must be launched via the shell.
        use_shell = sys.platform == "win32" and exe.lower().endswith((".cmd", ".bat"))
        self._proc = subprocess.Popen(
            subprocess.list2cmdline(args) if use_shell else args,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
            cwd=self.root, shell=use_shell, bufsize=0,
        )
        self._started_at = time.time()
        self._ready.clear()
        self._dead.clear()
        threading.Thread(target=self._reader, name="roslyn-reader", daemon=True).start()
        self._initialize()

    def _initialize(self) -> None:
        params = {
            "processId": os.getpid(),
            "rootUri": path_to_uri(self.root),
            "workspaceFolders": [{"uri": path_to_uri(self.root), "name": Path(self.root).name}],
            "clientInfo": {"name": "roslyn-mcp", "version": "0.1.0"},
            "capabilities": {
                "workspace": {
                    "workspaceFolders": True,
                    "configuration": True,
                    "applyEdit": False,
                    "workspaceEdit": {"documentChanges": True},
                },
                "textDocument": {
                    "synchronization": {"didSave": True},
                    "definition": {"linkSupport": True},
                    "references": {},
                    "hover": {"contentFormat": ["markdown", "plaintext"]},
                    "documentSymbol": {"hierarchicalDocumentSymbolSupport": True},
                    "rename": {"prepareSupport": True},
                    "diagnostic": {"dynamicRegistration": True},
                    "implementation": {"linkSupport": True},
                    "typeDefinition": {"linkSupport": True},
                    "codeAction": {},
                },
                "window": {"workDoneProgress": True},
            },
        }
        result = self.request("initialize", params, timeout=DEFAULT_READY_TIMEOUT)
        self.server_capabilities = result.get("capabilities", {})
        self.notify("initialized", {})

    def wait_ready(self, timeout: float = DEFAULT_READY_TIMEOUT) -> bool:
        """Block until Roslyn reports project load complete (or timeout)."""
        self.start()
        return self._ready.wait(timeout)

    def shutdown(self) -> None:
        if not self.alive:
            return
        try:
            self.request("shutdown", None, timeout=10)
            self.notify("exit", None)
        except Exception:
            pass
        finally:
            try:
                self._proc.wait(timeout=10)
            except Exception:
                self._proc.kill()
            self._dead.set()

    # ------------------------------------------------------------- transport
    def _send(self, msg: dict) -> None:
        if not self.alive:
            raise LspDead("roslyn-language-server is not running")
        body = json.dumps(msg).encode("utf-8")
        with self._write_lock:
            try:
                self._proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
                self._proc.stdin.flush()
            except (BrokenPipeError, OSError) as e:
                self._dead.set()
                raise LspDead(str(e)) from e

    def request(self, method: str, params: Any, timeout: float = DEFAULT_REQUEST_TIMEOUT) -> Any:
        rid = next(self._ids)
        ev, slot = threading.Event(), {}
        with self._lock:
            self._pending[rid] = (ev, slot)
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        if not ev.wait(timeout):
            with self._lock:
                self._pending.pop(rid, None)
            if not self.alive:
                raise LspDead(f"server died while waiting for {method}")
            raise TimeoutError(f"{method} timed out after {timeout}s")
        if "error" in slot:
            e = slot["error"]
            raise LspError(e.get("code", -1), e.get("message", "?"), e.get("data"))
        return slot.get("result")

    def notify(self, method: str, params: Any) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def _reader(self) -> None:
        out = self._proc.stdout
        try:
            while True:
                headers: dict[str, str] = {}
                while True:
                    line = out.readline()
                    if not line:
                        raise EOFError
                    line = line.decode("ascii", "replace").strip()
                    if not line:
                        break
                    k, _, v = line.partition(":")
                    headers[k.strip().lower()] = v.strip()
                length = int(headers.get("content-length", "0"))
                body = b""
                while len(body) < length:
                    chunk = out.read(length - len(body))
                    if not chunk:
                        raise EOFError
                    body += chunk
                try:
                    msg = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                self._dispatch(msg)
        except (EOFError, OSError, ValueError):
            pass
        finally:
            self._dead.set()
            self.exit_code = self._proc.poll()
            with self._lock:
                for ev, slot in self._pending.values():
                    slot["error"] = {"code": -32000, "message": "server exited"}
                    ev.set()
                self._pending.clear()

    def _dispatch(self, msg: dict) -> None:
        if "id" in msg and "method" in msg:            # server -> client request
            handler = self._handlers.get(msg["method"])
            try:
                result = handler(msg.get("params") or {}) if handler else None
                reply = {"jsonrpc": "2.0", "id": msg["id"], "result": result}
                if handler is None:
                    reply = {"jsonrpc": "2.0", "id": msg["id"],
                             "error": {"code": -32601, "message": f"unhandled {msg['method']}"}}
            except Exception as e:  # never let a handler kill the reader
                reply = {"jsonrpc": "2.0", "id": msg["id"],
                         "error": {"code": -32603, "message": str(e)}}
            try:
                self._send(reply)
            except LspDead:
                pass
        elif "id" in msg:                               # response
            with self._lock:
                entry = self._pending.pop(msg["id"], None)
            if entry:
                ev, slot = entry
                if "error" in msg:
                    slot["error"] = msg["error"]
                else:
                    slot["result"] = msg.get("result")
                ev.set()
        else:                                           # notification
            method = msg.get("method", "")
            if method == PROJECT_INIT_COMPLETE:
                self._ready.set()
            self.notifications.append(msg)
            del self.notifications[:-200]

    # ----------------------------------------------------------- documents
    def open(self, path: str) -> str:
        """didOpen the file (idempotent). Returns its uri."""
        uri = path_to_uri(path)
        if uri in self._open_docs:
            return uri
        text = Path(path).read_text(encoding="utf-8-sig")
        lang = "razor" if path.lower().endswith((".razor", ".cshtml")) else "csharp"
        self.notify("textDocument/didOpen", {"textDocument": {
            "uri": uri, "languageId": lang, "version": 1, "text": text}})
        self._open_docs[uri] = 1
        return uri

    def refresh(self, path: str) -> str:
        """Re-sync a file from disk if it is open (agent edited it)."""
        uri = path_to_uri(path)
        if uri not in self._open_docs:
            return self.open(path)
        v = self._open_docs[uri] + 1
        self._open_docs[uri] = v
        self.notify("textDocument/didChange", {
            "textDocument": {"uri": uri, "version": v},
            "contentChanges": [{"text": Path(path).read_text(encoding="utf-8-sig")}],
        })
        return uri

    def close(self, path: str) -> None:
        uri = path_to_uri(path)
        if self._open_docs.pop(uri, None) is not None:
            self.notify("textDocument/didClose", {"textDocument": {"uri": uri}})

    def close_all(self) -> None:
        for uri in list(self._open_docs):
            self.close(uri_to_path(uri))
