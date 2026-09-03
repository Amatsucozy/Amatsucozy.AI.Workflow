"""Tests for amtcz_mcp.server — tool registration and direct tool calls.

Note: mcp 2.0.0's MCPServer.tool() decorator registers the function with the
tool manager and returns the original function unchanged (see
mcp.server.mcpserver.server.MCPServer.tool -> decorator(fn): ... return fn),
so the decorated names in amtcz_mcp.server (sarif_probe, exp_inventory, etc.)
remain directly callable as plain Python functions.
"""

from __future__ import annotations

import asyncio

from amtcz_mcp.server import exp_inventory, mcp, sarif_probe

EXPECTED_TOOL_NAMES = [
    "exp_inventory",
    "exp_search",
    "sarif_build",
    "sarif_probe",
    "test_probe",
    "test_run",
]


def test_list_tools_names():
    # mcp 2.0.0: MCPServer.list_tools() is async.
    tools = asyncio.run(mcp.list_tools())
    names = sorted(t.name for t in tools)
    assert names == EXPECTED_TOOL_NAMES


def test_sarif_probe_direct_call_returns_plain_dict(tmp_path):
    result = sarif_probe(root=str(tmp_path))
    assert isinstance(result, dict)
    assert not hasattr(result, "__dataclass_fields__")
    assert result["verdict"] == "no_logs"


def test_exp_inventory_direct_call_returns_plain_dict(tmp_path):
    result = exp_inventory(root=str(tmp_path))
    assert isinstance(result, dict)
    assert not hasattr(result, "__dataclass_fields__")
    assert result["verdict"] == "no_entries"
