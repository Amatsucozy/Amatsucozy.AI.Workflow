"""SQL Server provider. Reads sys.* catalog views (INFORMATION_SCHEMA lacks
extended properties, index columns, and FK column pairing). pyodbc, one
connection, five queries, closed on exit.

Connection URL forms accepted (see providers/__init__.py):
  mssql://user:pass@host[:port]/database?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
  mssql://host/database?trusted_connection=yes
  raw ODBC string: Driver={ODBC Driver 18 for SQL Server};Server=host;Database=db;Uid=u;Pwd=p;...
"""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote, urlparse

from dbschema_mcp.model import Catalog, Column, DialectHints, ForeignKey, Index, Table
from dbschema_mcp.providers.base import SchemaProvider

_Q_TABLES = """
SELECT s.name, o.name, o.type, CAST(ep.value AS nvarchar(4000))
FROM sys.objects o
JOIN sys.schemas s ON s.schema_id = o.schema_id
LEFT JOIN sys.extended_properties ep
       ON ep.class = 1 AND ep.major_id = o.object_id AND ep.minor_id = 0 AND ep.name = 'MS_Description'
WHERE o.type IN ('U', 'V') AND o.is_ms_shipped = 0
ORDER BY s.name, o.name
"""

_Q_COLUMNS = """
SELECT s.name, o.name, c.column_id, c.name,
       t.name, c.max_length, c.precision, c.scale, c.is_nullable,
       dc.definition, CAST(ep.value AS nvarchar(4000)), c.is_identity, c.is_computed
FROM sys.columns c
JOIN sys.objects o ON o.object_id = c.object_id
JOIN sys.schemas s ON s.schema_id = o.schema_id
JOIN sys.types t ON t.user_type_id = c.user_type_id
LEFT JOIN sys.default_constraints dc ON dc.object_id = c.default_object_id
LEFT JOIN sys.extended_properties ep
       ON ep.class = 1 AND ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
WHERE o.type IN ('U', 'V') AND o.is_ms_shipped = 0
ORDER BY s.name, o.name, c.column_id
"""

_Q_KEYS = """
SELECT s.name, o.name, kc.name, kc.type, ic.key_ordinal, c.name
FROM sys.key_constraints kc
JOIN sys.objects o ON o.object_id = kc.parent_object_id
JOIN sys.schemas s ON s.schema_id = o.schema_id
JOIN sys.index_columns ic ON ic.object_id = kc.parent_object_id AND ic.index_id = kc.unique_index_id
JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
ORDER BY s.name, o.name, kc.name, ic.key_ordinal
"""

_Q_FKS = """
SELECT ps.name, po.name, fk.name, fkc.constraint_column_id,
       pc.name, rs.name, ro.name, rc.name
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.objects po ON po.object_id = fk.parent_object_id
JOIN sys.schemas ps ON ps.schema_id = po.schema_id
JOIN sys.columns pc ON pc.object_id = fkc.parent_object_id AND pc.column_id = fkc.parent_column_id
JOIN sys.objects ro ON ro.object_id = fk.referenced_object_id
JOIN sys.schemas rs ON rs.schema_id = ro.schema_id
JOIN sys.columns rc ON rc.object_id = fkc.referenced_object_id AND rc.column_id = fkc.referenced_column_id
ORDER BY ps.name, po.name, fk.name, fkc.constraint_column_id
"""

_Q_INDEXES = """
SELECT s.name, o.name, i.name, i.is_unique, ic.key_ordinal, c.name
FROM sys.indexes i
JOIN sys.objects o ON o.object_id = i.object_id
JOIN sys.schemas s ON s.schema_id = o.schema_id
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.key_ordinal > 0
JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
WHERE i.type > 0 AND i.is_primary_key = 0 AND i.is_unique_constraint = 0 AND i.is_hypothetical = 0
  AND o.type IN ('U', 'V') AND o.is_ms_shipped = 0
ORDER BY s.name, o.name, i.name, ic.key_ordinal
"""

_LENGTH_TYPES = {"char", "varchar", "binary", "varbinary"}
_NLENGTH_TYPES = {"nchar", "nvarchar"}
_PRECISION_SCALE = {"decimal", "numeric"}
_SCALE_ONLY = {"datetime2", "datetimeoffset", "time"}


def render_type(base: str, max_length: int, precision: int, scale: int) -> str:
    """Rebuild the declared type text the way SSMS shows it."""
    if base in _LENGTH_TYPES:
        return f"{base}({'max' if max_length == -1 else max_length})"
    if base in _NLENGTH_TYPES:
        return f"{base}({'max' if max_length == -1 else max_length // 2})"
    if base in _PRECISION_SCALE:
        return f"{base}({precision},{scale})"
    if base in _SCALE_ONLY:
        return f"{base}({scale})"
    return base


def build_odbc_string(url: str) -> str:
    """mssql://... URL -> ODBC connection string. Raw ODBC strings pass through."""
    if "://" not in url:
        return url
    u = urlparse(url)
    q = {k.lower(): v[0] for k, v in parse_qs(u.query).items()}
    driver = q.pop("driver", "ODBC Driver 18 for SQL Server")
    server = u.hostname or "localhost"
    if u.port:
        server = f"{server},{u.port}"
    parts = [f"Driver={{{driver}}}", f"Server={server}"]
    if u.path.strip("/"):
        parts.append(f"Database={unquote(u.path.strip('/'))}")
    if u.username:
        parts.append(f"Uid={unquote(u.username)}")
        parts.append(f"Pwd={unquote(u.password or '')}")
    elif "trusted_connection" not in q:
        q["trusted_connection"] = "yes"
    for k, v in q.items():
        parts.append(f"{k}={v}")
    return ";".join(parts)


class MssqlProvider(SchemaProvider):
    dialect = "mssql"

    def hints(self) -> DialectHints:
        return DialectHints(
            dialect="mssql",
            identifier_quote_open="[", identifier_quote_close="]",
            default_schema="dbo",
            row_limit_syntax="TOP (<n>) immediately after SELECT; OFFSET/FETCH requires ORDER BY",
            string_concat="+",
            notes=[
                "Identifiers are case-insensitive under the default collation; string comparisons usually are too.",
                "Booleans are bit 0/1, no true/false literals.",
                "Use GETDATE()/SYSUTCDATETIME(), not NOW().",
                "Views are listed with kind=view; indexed views share the same columns query.",
            ],
        )

    def load_catalog(self) -> Catalog:
        import pyodbc  # lazy: only required when this provider is selected

        conn = pyodbc.connect(build_odbc_string(self.url), readonly=True)
        try:
            cur = conn.cursor()
            dbname = cur.execute("SELECT DB_NAME()").fetchone()[0]
            allowed = {s.lower() for s in self.schemas}

            def wanted(schema: str) -> bool:
                return not allowed or schema.lower() in allowed

            tables: dict[str, Table] = {}
            for schema, name, otype, comment in cur.execute(_Q_TABLES).fetchall():
                if wanted(schema):
                    t = Table(schema, name, "view" if otype.strip() == "V" else "table", comment)
                    tables[t.key] = t

            for (schema, name, col_id, col, base, max_len, prec, scale, nullable,
                 default, comment, is_identity, is_computed) in cur.execute(_Q_COLUMNS).fetchall():
                t = tables.get(f"{schema}.{name}".lower())
                if not t:
                    continue
                if is_identity:
                    default = "IDENTITY"
                elif is_computed:
                    default = "COMPUTED"
                t.columns.append(Column(col, render_type(base, max_len, prec, scale),
                                        bool(nullable), default, comment, col_id))

            for schema, name, kname, ktype, _ord, col in cur.execute(_Q_KEYS).fetchall():
                t = tables.get(f"{schema}.{name}".lower())
                if not t:
                    continue
                if ktype.strip() == "PK":
                    t.primary_key.append(col)
                else:  # UQ
                    idx = next((i for i in t.indexes if i.name == kname), None)
                    if idx is None:
                        idx = Index(kname, True, [])
                        t.indexes.append(idx)
                    idx.columns.append(col)
            for t in tables.values():
                for c in t.columns:
                    c.is_pk = c.name in t.primary_key

            for (schema, name, fkname, _ord, col, rschema, rname, rcol) in cur.execute(_Q_FKS).fetchall():
                t = tables.get(f"{schema}.{name}".lower())
                if not t:
                    continue
                fk = next((f for f in t.foreign_keys if f.name == fkname), None)
                if fk is None:
                    fk = ForeignKey(fkname, [], rschema, rname, [])
                    t.foreign_keys.append(fk)
                fk.columns.append(col)
                fk.ref_columns.append(rcol)

            for schema, name, iname, unique, _ord, col in cur.execute(_Q_INDEXES).fetchall():
                t = tables.get(f"{schema}.{name}".lower())
                if not t:
                    continue
                idx = next((i for i in t.indexes if i.name == iname), None)
                if idx is None:
                    idx = Index(iname, bool(unique), [])
                    t.indexes.append(idx)
                idx.columns.append(col)
        finally:
            conn.close()

        return Catalog(
            dialect=self.dialect, database=dbname, hints=self.hints(), tables=tables,
            loaded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            schemas_filter=list(self.schemas),
        )
