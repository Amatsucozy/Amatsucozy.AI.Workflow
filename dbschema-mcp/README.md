# dbschema-mcp

Stdio MCP server that returns **database structure**, not data. The agent
asks "what table relates to X", "what is the column for Y", "how do I join
Z" - the server answers from a one-time catalog snapshot; the agent writes
the SQL. No query is ever executed against user tables.

Providers: PostgreSQL (`psycopg` 3, `pg_catalog`) and SQL Server (`pyodbc`,
`sys.*`). Everything above the provider is dialect-agnostic.

Runs as a plain Python process over stdio — no Docker, no container image.
The database driver is an extra, so install the one you need: `[postgres]`,
`[mssql]`, or `[all]`. SQL Server additionally needs an ODBC driver on the
host (`ODBC Driver 18 for SQL Server` by default).

## Install

Using [uv](https://docs.astral.sh/uv/) (preferred):

```bash
uv tool install "dbschema-mcp[postgres] @ <path-or-git-url>/dbschema-mcp"
```

Or skip installing entirely and run it ad hoc — uv fetches/builds into a
cached environment on first use and reuses it after:

```bash
uvx --from "dbschema-mcp[postgres] @ <path-or-git-url>/dbschema-mcp" dbschema-mcp
```

Without uv, plain pip works too:

```bash
pipx install "dbschema-mcp[postgres] @ git+https://.../dbschema-mcp"
pip install --user "dbschema-mcp[mssql] @ git+https://.../dbschema-mcp"
```

Any of the above generates a native `dbschema-mcp` entry point. If it isn't
resolving on PATH in whatever environment your MCP client spawns from,
`python -m dbschema_mcp` runs the server directly, independent of PATH.

## Configure

Environment only - no credentials in tool calls, and no tool takes a
connection parameter (there's a test that enforces that).

| Var | Value |
|---|---|
| `DBSCHEMA_URL` | `postgresql://user:pass@host/db` or `mssql://user:pass@host:1433/db?TrustServerCertificate=yes` or a raw ODBC string |
| `DBSCHEMA_SCHEMAS` | optional comma list, e.g. `dbo,sales` |

`DBSCHEMA_URL` is unset at startup produces a warning on stderr and a
`catalog_unavailable` verdict from every tool — the server still starts, so
the client sees a live server rather than a spawn failure.

## Registering in a consumer's MCP config

Copy [`.mcp.json.example`](.mcp.json.example) to your target repo's
`.mcp.json` (or merge the `dbschema` entry into an existing one). With
`uvx`, no separate install step is needed:

```json
{
  "mcpServers": {
    "dbschema": {
      "command": "uvx",
      "args": [
        "--from",
        "dbschema-mcp[postgres] @ git+https://github.com/Amatsucozy/Amatsucozy.AI.Workflow.git@main#subdirectory=dbschema-mcp",
        "dbschema-mcp"
      ],
      "env": { "DBSCHEMA_URL": "postgresql://app:secret@localhost/shop" }
    }
  }
}
```

If you installed with `uv tool install` (or pip/pipx) instead, the entry
point is already on PATH:

```json
{
  "mcpServers": {
    "dbschema": {
      "command": "dbschema-mcp",
      "env": { "DBSCHEMA_URL": "postgresql://app:secret@localhost/shop" }
    }
  }
}
```

Fallback if neither resolves on PATH in the client's spawn environment:

```json
{
  "mcpServers": {
    "dbschema": {
      "command": "python",
      "args": ["-m", "dbschema_mcp"],
      "env": { "DBSCHEMA_URL": "postgresql://app:secret@localhost/shop" }
    }
  }
}
```

A committed `.mcp.json` with a real `DBSCHEMA_URL` puts credentials in git.
Point it at a read-only account, or have your client inject the variable
from the environment instead.

## Tools at a glance

| Tool | Question it answers |
|---|---|
| `catalog_info` | Which engine, which dialect rules apply, how big is it. Call first. |
| `catalog_refresh` | Re-introspect after a migration. Fails closed — never serves a stale snapshot. |
| `schema_search_tables` | "What table holds X?" - ranked, with `matched_on` reasons. |
| `schema_search_columns` | "What is the column for Y?" |
| `schema_describe_table` | Authoritative columns/PK/FK/indexes + inbound FKs. Write SQL from this. |
| `schema_related_tables` | Join graph with `join_on` predicates and multi-hop `path`. |
| `schema_list_tables` | Flat inventory when search misses. |

Every result carries `verdict`; every snapshot-backed result carries
`loaded_at`. Each tool's full docstring (parameter behavior and every
`verdict` value's meaning) is visible to the calling agent through MCP tool
introspection.

For the cross-tool judgment calls that don't belong in any single tool's
description, merge [`CLAUDE.md.example`](CLAUDE.md.example) into the
consuming repository's `CLAUDE.md`.

## Expected agent flow

1. `catalog_info` -> read `hints` (quoting, default schema, TOP vs LIMIT).
2. `schema_search_tables("invoice")` -> pick hit.
3. `schema_describe_table("Invoices")` + `schema_related_tables("Invoices", 1)`.
4. Compose SQL from columns + `join_on`. Nothing here runs it.

## Local development

From inside `dbschema-mcp/`:

```bash
uv sync --extra dev --extra all
```

This creates `.venv/` and `uv.lock` (committed, for reproducible dev
installs). Run the server with `uv run dbschema-mcp` (or
`uv run python -m dbschema_mcp`), and the test suite with `uv run pytest`.

Without uv: `pip install -e ".[all,dev]"`, then `dbschema-mcp` /
`python -m dbschema_mcp` / `pytest` as usual.

```bash
pytest -q        # no database required; providers are exercised only for URL/type rendering
```

The suite runs entirely against a hand-built catalog (see
`tests/conftest.py`), so it needs neither a database nor a driver.
`tests/test_server.py` pins the tool surface: the exact registered names,
that every tool documents its verdicts, that results are plain
JSON-serialisable dicts, and that no tool accepts a credential parameter.
