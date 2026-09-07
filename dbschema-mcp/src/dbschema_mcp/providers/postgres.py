"""PostgreSQL provider. Reads pg_catalog directly (information_schema drops
comments, expression defaults, and partitioned tables). psycopg 3, one
connection, four queries, closed on exit.
"""
from __future__ import annotations

from datetime import datetime, timezone

from dbschema_mcp.model import Catalog, Column, DialectHints, ForeignKey, Index, Table
from dbschema_mcp.providers.base import SchemaProvider

_SYSTEM = ("pg_catalog", "information_schema", "pg_toast")
_RELKINDS = ("r", "p", "v", "m")  # table, partitioned table, view, materialized view

_Q_TABLES = """
SELECT n.nspname, c.relname, c.relkind, obj_description(c.oid, 'pg_class')
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = ANY(%(kinds)s)
  AND n.nspname <> ALL(%(system)s)
  AND n.nspname NOT LIKE 'pg_temp%%'
  AND (%(all_schemas)s OR n.nspname = ANY(%(schemas)s))
ORDER BY 1, 2
"""

_Q_COLUMNS = """
SELECT n.nspname, c.relname, a.attnum, a.attname,
       format_type(a.atttypid, a.atttypmod), NOT a.attnotnull,
       pg_get_expr(d.adbin, d.adrelid), col_description(c.oid, a.attnum)
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
WHERE a.attnum > 0 AND NOT a.attisdropped
  AND c.relkind = ANY(%(kinds)s)
  AND n.nspname <> ALL(%(system)s)
  AND (%(all_schemas)s OR n.nspname = ANY(%(schemas)s))
ORDER BY 1, 2, 3
"""

_Q_CONSTRAINTS = """
SELECT con.conname, con.contype, n.nspname, c.relname,
       array_agg(a.attname ORDER BY k.ord),
       fn.nspname, fc.relname,
       array_agg(fa.attname ORDER BY k.ord)
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
CROSS JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord)
JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum
LEFT JOIN pg_class fc ON fc.oid = con.confrelid
LEFT JOIN pg_namespace fn ON fn.oid = fc.relnamespace
LEFT JOIN LATERAL unnest(con.confkey) WITH ORDINALITY AS fk(attnum, ord) ON fk.ord = k.ord
LEFT JOIN pg_attribute fa ON fa.attrelid = con.confrelid AND fa.attnum = fk.attnum
WHERE con.contype IN ('p', 'f', 'u')
  AND n.nspname <> ALL(%(system)s)
  AND (%(all_schemas)s OR n.nspname = ANY(%(schemas)s))
GROUP BY con.oid, con.conname, con.contype, n.nspname, c.relname, fn.nspname, fc.relname
ORDER BY 3, 4, 1
"""

_Q_INDEXES = """
SELECT n.nspname, t.relname, i.relname, ix.indisunique,
       array_agg(COALESCE(a.attname, '<expr>') ORDER BY k.ord)
FROM pg_index ix
JOIN pg_class t ON t.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_namespace n ON n.oid = t.relnamespace
CROSS JOIN LATERAL unnest(ix.indkey) WITH ORDINALITY AS k(attnum, ord)
LEFT JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum AND k.attnum > 0
WHERE NOT ix.indisprimary
  AND n.nspname <> ALL(%(system)s)
  AND (%(all_schemas)s OR n.nspname = ANY(%(schemas)s))
GROUP BY n.nspname, t.relname, i.relname, ix.indisunique
ORDER BY 1, 2, 3
"""


class PostgresProvider(SchemaProvider):
    dialect = "postgres"

    def hints(self) -> DialectHints:
        return DialectHints(
            dialect="postgres",
            identifier_quote_open='"', identifier_quote_close='"',
            default_schema="public",
            row_limit_syntax="LIMIT <n> at the end of the query (after ORDER BY)",
            string_concat="||",
            notes=[
                "Unquoted identifiers fold to lower case; quote mixed-case names exactly as returned.",
                "Booleans are true/false literals; use ILIKE for case-insensitive matching.",
                "kind=view rows may be materialized views (no distinction in this catalog).",
            ],
        )

    def load_catalog(self) -> Catalog:
        import psycopg  # lazy: only required when this provider is selected

        params = {
            "kinds": list(_RELKINDS),
            "system": list(_SYSTEM),
            "all_schemas": not self.schemas,
            "schemas": self.schemas or [""],
        }
        tables: dict[str, Table] = {}
        with psycopg.connect(self.url, autocommit=True) as conn:
            dbname = conn.info.dbname
            with conn.cursor() as cur:
                cur.execute(_Q_TABLES, params)
                for schema, name, relkind, comment in cur.fetchall():
                    t = Table(schema, name, "view" if relkind in ("v", "m") else "table", comment)
                    tables[t.key] = t

                cur.execute(_Q_COLUMNS, params)
                for schema, name, attnum, col, dtype, nullable, default, comment in cur.fetchall():
                    t = tables.get(f"{schema}.{name}".lower())
                    if t:
                        t.columns.append(Column(col, dtype, bool(nullable), default, comment, attnum))

                cur.execute(_Q_CONSTRAINTS, params)
                for cname, ctype, schema, name, cols, fschema, fname, fcols in cur.fetchall():
                    t = tables.get(f"{schema}.{name}".lower())
                    if not t:
                        continue
                    if ctype == "p":
                        t.primary_key = list(cols)
                        for c in t.columns:
                            c.is_pk = c.name in t.primary_key
                    elif ctype == "f":
                        t.foreign_keys.append(ForeignKey(cname, list(cols), fschema, fname, list(fcols)))
                    elif ctype == "u":
                        t.indexes.append(Index(cname, True, list(cols)))

                cur.execute(_Q_INDEXES, params)
                for schema, name, iname, unique, cols in cur.fetchall():
                    t = tables.get(f"{schema}.{name}".lower())
                    if t and not any(i.name == iname for i in t.indexes):
                        t.indexes.append(Index(iname, bool(unique), list(cols)))

        return Catalog(
            dialect=self.dialect, database=dbname, hints=self.hints(), tables=tables,
            loaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            schemas_filter=list(self.schemas),
        )
