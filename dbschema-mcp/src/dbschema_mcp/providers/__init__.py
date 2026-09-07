"""Provider registry keyed by connection-URL scheme.

  postgresql://  postgres://          -> PostgresProvider  (psycopg 3)
  mssql://  sqlserver://              -> MssqlProvider     (pyodbc)
  raw ODBC string (contains ';' and '=' and no '://') -> MssqlProvider

Imports are lazy so the server starts with only the driver you installed.
"""
from __future__ import annotations

from dbschema_mcp.providers.base import SchemaProvider


def detect_dialect(url: str) -> str:
    low = url.strip().lower()
    if low.startswith(("postgresql://", "postgres://")):
        return "postgres"
    if low.startswith(("mssql://", "sqlserver://")):
        return "mssql"
    if "://" not in low and ";" in low and "=" in low:
        return "mssql"
    raise ValueError(
        f"Unrecognised connection URL scheme: {url.split('://')[0] if '://' in url else url[:20]!r}. "
        "Expected postgresql://, mssql://, or a raw ODBC connection string.")


def make_provider(url: str, schemas: list[str] | None = None) -> SchemaProvider:
    dialect = detect_dialect(url)
    if dialect == "postgres":
        from dbschema_mcp.providers.postgres import PostgresProvider
        return PostgresProvider(url, schemas)
    from dbschema_mcp.providers.mssql import MssqlProvider
    return MssqlProvider(url, schemas)
