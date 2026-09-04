"""Tests for dbschema_mcp.server — tool registration, the verdict contract,
and direct tool calls.

Note: the `mcp` high-level server's tool() decorator registers the function
with the tool manager and returns the original function unchanged, so the
decorated names in dbschema_mcp.server (catalog_info, schema_search_tables,
etc.) remain directly callable as plain Python functions. That property is
what lets every test below drive the tools without a transport — and what
lets catalog_refresh delegate to catalog_info in the first place.

Nothing here touches a database: the module-level snapshot is replaced with
the synthetic SchemaIndex from conftest.
"""
from __future__ import annotations

import asyncio
import json

import pytest

from dbschema_mcp import server
from dbschema_mcp.catalog import SchemaIndex

EXPECTED_TOOL_NAMES = [
    "catalog_info",
    "catalog_refresh",
    "schema_describe_table",
    "schema_list_tables",
    "schema_related_tables",
    "schema_search_columns",
    "schema_search_tables",
]


def _input_schema(tool) -> dict:
    # mcp 2.x exposes input_schema; 1.x exposed inputSchema.
    return getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", {})


@pytest.fixture(autouse=True)
def isolated_snapshot(monkeypatch):
    """Every test starts with no snapshot and no DBSCHEMA_URL, so nothing can
    reach a real database even if the developer has one configured."""
    monkeypatch.delenv("DBSCHEMA_URL", raising=False)
    monkeypatch.delenv("DBSCHEMA_SCHEMAS", raising=False)
    monkeypatch.setattr(server, "_index", None)
    monkeypatch.setattr(server, "_load_error", None)


@pytest.fixture
def loaded(monkeypatch, sample_catalog):
    """Install the synthetic catalog as the server's snapshot."""
    monkeypatch.setattr(server, "_index", SchemaIndex(sample_catalog))
    return sample_catalog


def all_tool_calls():
    """One representative call per tool, for the contract tests that must
    cover the whole surface rather than a sampled subset."""
    return [
        ("catalog_info", lambda: server.catalog_info()),
        ("catalog_refresh", lambda: server.catalog_refresh()),
        ("schema_search_tables", lambda: server.schema_search_tables("customer")),
        ("schema_search_columns", lambda: server.schema_search_columns("email")),
        ("schema_describe_table", lambda: server.schema_describe_table("Orders")),
        ("schema_related_tables", lambda: server.schema_related_tables("Orders")),
        ("schema_list_tables", lambda: server.schema_list_tables()),
    ]


# --- registration -------------------------------------------------------------

def test_list_tools_names():
    # mcp 2.x: list_tools() is async.
    tools = asyncio.run(server.mcp.list_tools())
    assert sorted(t.name for t in tools) == EXPECTED_TOOL_NAMES


def test_every_tool_declares_its_verdict_meanings():
    """The verdict block is the tool contract — an agent picks its next move
    from it, so a tool without one is a convention break, not a style nit."""
    tools = asyncio.run(server.mcp.list_tools())
    missing = [t.name for t in tools if "verdict meanings:" not in (t.description or "")]
    assert missing == []


def test_documented_verdicts_are_reachable_names():
    """Guards against a docstring drifting from the code: every verdict string
    the module can actually return must be mentioned in some docstring."""
    tools = {t.name: (t.description or "") for t in asyncio.run(server.mcp.list_tools())}
    expected = {
        "catalog_info": ["ok", "catalog_unavailable"],
        "catalog_refresh": ["catalog_info"],
        "schema_search_tables": ["ok", "no_match", "catalog_unavailable"],
        "schema_search_columns": ["ok", "no_match", "table_not_found", "table_ambiguous",
                                  "catalog_unavailable"],
        "schema_describe_table": ["ok", "not_found", "ambiguous", "catalog_unavailable"],
        "schema_related_tables": ["ok", "no_relations", "not_found", "ambiguous",
                                  "catalog_unavailable"],
        "schema_list_tables": ["ok", "empty", "catalog_unavailable"],
    }
    for name, verdicts in expected.items():
        for v in verdicts:
            assert v in tools[name], f"{name} docstring never mentions {v!r}"


def test_no_tool_takes_a_credential_parameter():
    """Credentials are environment-only by design; a connection parameter on a
    tool would put them in the agent's transcript."""
    banned = {"url", "dsn", "connection_string", "password", "user", "username"}
    for tool in asyncio.run(server.mcp.list_tools()):
        params = set((_input_schema(tool).get("properties") or {}).keys())
        assert not (params & banned), f"{tool.name} exposes {params & banned}"


# --- contract across every tool -----------------------------------------------

@pytest.mark.parametrize("name,call", all_tool_calls(), ids=lambda v: v if isinstance(v, str) else "")
def test_returns_plain_json_serialisable_dict(loaded, name, call):
    result = call()
    assert isinstance(result, dict)
    assert not hasattr(result, "__dataclass_fields__")
    json.dumps(result)  # must survive MCP serialisation


@pytest.mark.parametrize(
    "name,call",
    # catalog_refresh is excluded by design: it always re-reads the database
    # rather than answering from the installed snapshot, so with no
    # DBSCHEMA_URL it correctly returns catalog_unavailable (no loaded_at).
    [c for c in all_tool_calls() if c[0] != "catalog_refresh"],
    ids=lambda v: v if isinstance(v, str) else "")
def test_snapshot_backed_results_carry_loaded_at(loaded, name, call):
    assert call()["loaded_at"] == loaded.loaded_at


@pytest.mark.parametrize("name,call", all_tool_calls(), ids=lambda v: v if isinstance(v, str) else "")
def test_unconfigured_returns_catalog_unavailable(name, call):
    result = call()
    assert result["verdict"] == "catalog_unavailable"
    assert result["error"] == "DBSCHEMA_URL is not set"


def test_bad_url_is_a_verdict_not_an_exception(monkeypatch):
    monkeypatch.setenv("DBSCHEMA_URL", "not-a-supported-scheme")
    result = server.catalog_info()
    assert result["verdict"] == "catalog_unavailable"
    assert "ValueError" in result["error"]


# --- per-tool verdicts --------------------------------------------------------

def test_catalog_info_reports_hints_and_counts(loaded):
    r = server.catalog_info()
    assert r["verdict"] == "ok"
    assert r["dialect"] == "mssql" and r["database"] == "shop"
    assert r["hints"]["default_schema"] == "dbo"
    assert r["hints"]["row_limit_syntax"].startswith("TOP")
    assert r["schemas"] == ["archive", "catalog", "dbo"]
    assert r["table_count"] == 6 and r["view_count"] == 0


def test_catalog_refresh_reloads_and_fails_closed(loaded):
    # No DBSCHEMA_URL, so a refresh must discard the snapshot rather than
    # keep serving the old one.
    assert server.catalog_refresh()["verdict"] == "catalog_unavailable"
    assert server.schema_list_tables()["verdict"] == "catalog_unavailable"


def test_search_tables_ok_and_no_match(loaded):
    ok = server.schema_search_tables("customer")
    assert ok["verdict"] == "ok" and ok["hits"][0]["table"] == "dbo.Customers"
    assert server.schema_search_tables("zzzz")["verdict"] == "no_match"


def test_search_columns_table_filter_verdicts(loaded):
    assert server.schema_search_columns("id", table="Orders")["verdict"] == "ok"
    assert server.schema_search_columns("id", table="Nope")["verdict"] == "table_not_found"
    amb = server.schema_search_columns("id", table="Products")
    assert amb["verdict"] == "table_ambiguous"
    assert sorted(amb["candidates"]) == ["archive.Products", "catalog.Products"]
    assert server.schema_search_columns("zzzz")["verdict"] == "no_match"


def test_describe_table_ok_not_found_ambiguous(loaded):
    ok = server.schema_describe_table("Orders")
    assert ok["verdict"] == "ok" and ok["qualified"] == "dbo.Orders"
    assert [c["name"] for c in ok["columns"] if c["is_pk"]] == ["OrderId"]
    assert ok["foreign_keys"][0]["ref_table"] == "Customers"
    assert [i["from_table"] for i in ok["inbound_foreign_keys"]] == ["dbo.OrderItems"]
    assert server.schema_describe_table("Nope")["verdict"] == "not_found"
    assert server.schema_describe_table("Products")["verdict"] == "ambiguous"


def test_related_tables_ok_depth_and_no_relations(loaded):
    d1 = server.schema_related_tables("Orders")
    assert d1["verdict"] == "ok" and d1["depth"] == 1
    assert {r["table"] for r in d1["relations"]} == {"dbo.Customers", "dbo.OrderItems"}
    d9 = server.schema_related_tables("Orders", depth=9)
    assert d9["depth"] == 4, "depth must be capped at 4"
    assert server.schema_related_tables("archive.Orders")["verdict"] == "no_relations"
    assert server.schema_related_tables("Nope")["verdict"] == "not_found"


def test_list_tables_filters_and_empty(loaded):
    everything = server.schema_list_tables()
    assert everything["verdict"] == "ok"
    assert everything["total"] == 6 and everything["shown"] == 6
    assert server.schema_list_tables(schema="dbo")["total"] == 3
    assert server.schema_list_tables(kind="view")["verdict"] == "empty"
    capped = server.schema_list_tables(max_results=2)
    assert capped["total"] == 6 and capped["shown"] == 2
