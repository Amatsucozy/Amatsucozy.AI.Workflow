"""dbschema-mcp server — exposes database structure retrieval over MCP
(stdio transport).

Returns schema, never data: no query is ever executed against user tables.
Each tool below wraps the pure indexing logic in catalog.py over a snapshot
taken by a provider, and returns a plain dict (dataclasses.asdict of the
module's result dataclasses) — the `verdict` field carries the outcome
semantics, the same contract amtcz-mcp's tools use.

Configuration is environment only (credentials never travel through tool
parameters):
  DBSCHEMA_URL       required. postgresql://..., mssql://..., or a raw ODBC string.
  DBSCHEMA_SCHEMAS   optional. Comma-separated schema allow-list (default: all non-system).

The catalog is snapshotted on first tool call and held in memory. Every
result carries `verdict`; every result that depends on the snapshot carries
`loaded_at` so the agent can decide whether to call catalog_refresh.
"""
from __future__ import annotations

import os
import sys
from dataclasses import asdict
from typing import Any

from dbschema_mcp import VERSION
from dbschema_mcp.catalog import SchemaIndex
from dbschema_mcp.providers import make_provider

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _Server  # type: ignore[no-redef]

mcp = _Server("dbschema")

_index: SchemaIndex | None = None
_load_error: str | None = None


def _load(force: bool = False) -> SchemaIndex | None:
    global _index, _load_error
    if _index is not None and not force:
        return _index
    # A forced reload fails closed: drop the old snapshot before attempting the
    # new one, so a refresh that can't reach the database reports
    # catalog_unavailable instead of silently serving pre-migration structure.
    if force:
        _index = None
    url = os.environ.get("DBSCHEMA_URL", "").strip()
    if not url:
        _load_error = "DBSCHEMA_URL is not set"
        return None
    schemas = [s.strip() for s in os.environ.get("DBSCHEMA_SCHEMAS", "").split(",") if s.strip()]
    try:
        provider = make_provider(url, schemas)
        _index = SchemaIndex(provider.load_catalog())
        _load_error = None
    except Exception as exc:  # noqa: BLE001 - surfaced as a verdict, never as a crash
        _index = None
        _load_error = f"{type(exc).__name__}: {exc}"
    return _index


def _not_loaded() -> dict[str, Any]:
    return {"verdict": "catalog_unavailable", "error": _load_error}


def _stamp(idx: SchemaIndex, payload: dict[str, Any]) -> dict[str, Any]:
    payload["loaded_at"] = idx.catalog.loaded_at
    return payload


# --- tools -------------------------------------------------------------------

@mcp.tool()
def catalog_info(refresh: bool = False) -> dict[str, Any]:
    """Connection, dialect, and size of the schema snapshot. Call this first in
    a session — the `hints` it returns are what make the SQL you write valid
    for this engine, and no other tool repeats them.

    Returns the DialectHints the agent must apply when writing SQL for this
    engine (identifier quoting, default schema, row-limit syntax, concat
    operator, notes), plus table/view counts and the schema list.

    refresh=True re-reads the database. Prefer catalog_refresh for that — it
    says what it does at the call site; this flag exists so a first call can
    force a fresh snapshot in one step.

    verdict meanings:
      "ok" - snapshot is loaded; see hints, schemas, table_count, view_count.
        loaded_at is the snapshot time — compare it against any migration you
        know landed this session before trusting the rest.
      "catalog_unavailable" - no snapshot could be taken; see `error` for the
        cause (DBSCHEMA_URL unset, driver not installed, connection refused,
        bad credentials). Every other tool returns this same verdict until it
        is resolved — an environment/config problem, so surface it to the
        human rather than retrying other tools in the hope one works.
    """
    idx = _load(force=refresh)
    if idx is None:
        return _not_loaded()
    cat = idx.catalog
    schemas = sorted({t.schema for t in cat.tables.values()})
    return _stamp(idx, {
        "verdict": "ok",
        "server_version": VERSION,
        "dialect": cat.dialect,
        "database": cat.database,
        "hints": asdict(cat.hints),
        "schemas": schemas,
        "schemas_filter": cat.schemas_filter,
        "table_count": sum(1 for t in cat.tables.values() if t.kind == "table"),
        "view_count": sum(1 for t in cat.tables.values() if t.kind == "view"),
    })


@mcp.tool()
def catalog_refresh() -> dict[str, Any]:
    """Discard the in-memory snapshot and re-introspect the database.

    Use after a migration ran this session, or when describe/search results
    contradict what the database evidently has. Not needed otherwise: the
    snapshot is taken once per server process and schema rarely changes
    mid-session — never call this between ordinary lookups.

    verdict meanings: same as catalog_info ("ok" with the new counts, or
    "catalog_unavailable" with `error`). A refresh that fails leaves no
    snapshot at all — the previous one is discarded first, so subsequent
    lookups return "catalog_unavailable" rather than stale data.
    """
    return catalog_info(refresh=True)


@mcp.tool()
def schema_search_tables(query: str, max_results: int = 10) -> dict[str, Any]:
    """Find tables/views related to a concept. Answers "what table holds X?".
    Start here when you know the domain word but not the table name; use
    schema_list_tables instead when you need to eyeball the whole namespace.

    query: free text - a domain word, a guessed table name, or a column name.
      Tokenised on snake_case/PascalCase/spaces, plural-folded (orders == order).
    Ranking is mechanical: exact name > name token > name substring > column
    token > comment token. `matched_on` explains each hit ("name:order",
    "column:customer_id", "comment:invoice").

    Follow up with schema_describe_table on the chosen hit; do not guess
    columns from the hit alone — a hit reports only why it matched, never the
    full column list.

    verdict meanings:
      "ok" - at least one hit; see hits (ranked, best first). A high score is
        not proof of the right table — read `matched_on` to see whether it
        matched on the name or only on an incidental column.
      "no_match" - nothing scored above zero. Not an error: try a different
        domain word, or call schema_list_tables to see what the namespace
        actually contains before guessing again.
      "catalog_unavailable" - no snapshot; see catalog_info.
    """
    idx = _load()
    if idx is None:
        return _not_loaded()
    hits = idx.search_tables(query, max(1, min(max_results, 50)))
    return _stamp(idx, {
        "verdict": "ok" if hits else "no_match",
        "query": query,
        "hits": [asdict(h) for h in hits],
    })


@mcp.tool()
def schema_search_columns(query: str, max_results: int = 20,
                          table: str | None = None) -> dict[str, Any]:
    """Find columns by name/comment across the database. Answers "what is the
    column for Y?". Prefer schema_describe_table when you already know the
    table — this searches broadly and returns matches only, not full
    definitions.

    query: free text, tokenised like schema_search_tables. Returns owning
      table, exact column name, declared type, nullability, PK flag, and
      `matched_on`.
    table: optional - restrict to one table (bare or schema-qualified name).

    verdict meanings:
      "ok" - at least one column matched; see hits.
      "no_match" - nothing scored. Not an error.
      "table_not_found" - the `table` filter named a table that isn't in the
        snapshot; the search never ran. Fix the name (or drop the filter)
        rather than retrying as-is.
      "table_ambiguous" - the `table` filter resolved to several schemas; see
        `candidates` and re-call with one of those qualified names.
      "catalog_unavailable" - no snapshot; see catalog_info.
    """
    idx = _load()
    if idx is None:
        return _not_loaded()
    if table:
        r = idx.resolve(table)
        if r.verdict != "ok":
            return _stamp(idx, {"verdict": f"table_{r.verdict}", "table": table,
                                "candidates": r.candidates})
    hits = idx.search_columns(query, max(1, min(max_results, 100)), table)
    return _stamp(idx, {
        "verdict": "ok" if hits else "no_match",
        "query": query,
        "hits": [asdict(h) for h in hits],
    })


@mcp.tool()
def schema_describe_table(table: str) -> dict[str, Any]:
    """Full definition of one table or view: columns (name, type, nullable,
    default, comment, is_pk), primary key, foreign keys (with referenced
    table/columns), indexes, and inbound foreign keys from other tables.

    This is the authoritative column list — write SQL from this, never from
    schema_search_tables/schema_search_columns hits, which report only what
    matched.

    table: bare name ("Orders", "order_item") or qualified ("sales.Orders").
      Bare names resolve case-insensitively, then by plural/case folding, then
      prefer the dialect default schema when several schemas match.

    verdict meanings:
      "ok" - the full definition follows, plus `qualified` and
        `inbound_foreign_keys`.
      "not_found" - no table resolved. Check spelling, or call
        schema_list_tables / schema_search_tables to find the real name —
        re-calling with the same string will not succeed.
      "ambiguous" - the bare name exists in several schemas and none is the
        dialect default; see `candidates` and re-call with a qualified name.
      "catalog_unavailable" - no snapshot; see catalog_info.
    """
    idx = _load()
    if idx is None:
        return _not_loaded()
    r = idx.resolve(table)
    if r.verdict != "ok":
        return _stamp(idx, {"verdict": r.verdict, "table": table, "candidates": r.candidates})
    t = r.table
    inbound = [
        {"from_table": o.qualified, "fk": fk.name, "columns": fk.columns,
         "ref_columns": fk.ref_columns}
        for o in idx.catalog.tables.values()
        for fk in o.foreign_keys
        if f"{fk.ref_schema}.{fk.ref_table}".lower() == t.key
    ]
    payload = asdict(t)
    payload["qualified"] = t.qualified
    payload["inbound_foreign_keys"] = inbound
    payload["verdict"] = "ok"
    return _stamp(idx, payload)


@mcp.tool()
def schema_related_tables(table: str, depth: int = 1,
                          max_results: int = 50) -> dict[str, Any]:
    """Tables reachable from `table` over foreign keys, with ready-to-use join
    predicates. Answers "write a query to view entity Z" — gives the join
    graph; the agent composes the SELECT. Pair it with
    schema_describe_table: this gives the joins, that gives the columns.

    depth: 1 = direct FKs only (default). 2-4 = transitive. Capped at 4.
      Raise it only when a direct join genuinely doesn't reach the entity you
      need — depth 3+ on a normalised schema returns most of the database.
    Each relation has: table, distance, direction ("outbound" = `table` holds
    the FK, "inbound" = the neighbour holds it), via_fk, join_on
    ("s.a.col = s.b.col" pairs joined by AND), and path (join_on chain from
    the origin, for multi-hop joins).

    verdict meanings:
      "ok" - see relations, ordered by distance then direction.
      "no_relations" - the table exists but has no FK edges at this depth.
        Either it is genuinely standalone or the schema declares no FK
        constraints — in the latter case join columns must be inferred from
        schema_describe_table by name, not assumed absent.
      "not_found" / "ambiguous" - same meaning and same fix as
        schema_describe_table (see `candidates` for the ambiguous case).
      "catalog_unavailable" - no snapshot; see catalog_info.
    """
    idx = _load()
    if idx is None:
        return _not_loaded()
    r = idx.resolve(table)
    if r.verdict != "ok":
        return _stamp(idx, {"verdict": r.verdict, "table": table, "candidates": r.candidates})
    rels = idx.related(r.table, depth, max(1, min(max_results, 200)))
    return _stamp(idx, {
        "verdict": "ok" if rels else "no_relations",
        "table": r.table.qualified,
        "depth": max(1, min(depth, 4)),
        "relations": [asdict(x) for x in rels],
    })


@mcp.tool()
def schema_list_tables(schema: str | None = None, kind: str | None = None,
                       max_results: int = 200) -> dict[str, Any]:
    """Flat inventory of tables/views: qualified name, kind, column count,
    comment.

    Use when schema_search_tables returns "no_match" and you need to eyeball
    the namespace — not as a first move on a large database, where a search
    is cheaper and better ranked. schema filters to one schema; kind is
    "table" or "view".

    verdict meanings:
      "ok" - see tables. `total` is the unfiltered count and `shown` is how
        many are in this response — if they differ, narrow with schema/kind
        rather than raising max_results.
      "empty" - the filters matched nothing. Check `schema`/`kind` spelling
        against catalog_info's schema list before concluding the database is
        empty.
      "catalog_unavailable" - no snapshot; see catalog_info.
    """
    idx = _load()
    if idx is None:
        return _not_loaded()
    rows = [
        {"table": t.qualified, "kind": t.kind, "column_count": len(t.columns),
         "comment": t.comment}
        for t in sorted(idx.catalog.tables.values(), key=lambda t: t.key)
        if (not schema or t.schema.lower() == schema.lower()) and (not kind or t.kind == kind)
    ]
    total = len(rows)
    rows = rows[: max(1, min(max_results, 1000))]
    return _stamp(idx, {
        "verdict": "ok" if rows else "empty",
        "total": total,
        "shown": len(rows),
        "tables": rows,
    })


def main() -> None:
    if not os.environ.get("DBSCHEMA_URL"):
        # Fail loud at process start; the tools would only ever return
        # catalog_unavailable. stderr, never stdout — stdout is the transport.
        print("dbschema-mcp: DBSCHEMA_URL is not set", file=sys.stderr)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
