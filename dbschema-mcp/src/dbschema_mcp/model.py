"""Normalized, dialect-agnostic schema model.

Providers fill this; catalog.py indexes it; server.py serialises it with
dataclasses.asdict(). Nothing dialect-specific lives here except the
DialectHints record, which is deliberately data (so the agent reads it) rather
than behaviour (so nothing here ever generates SQL).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Column:
    name: str
    data_type: str            # engine-native rendering, e.g. "nvarchar(50)", "timestamp with time zone"
    nullable: bool
    default: str | None = None
    comment: str | None = None
    ordinal: int = 0
    is_pk: bool = False


@dataclass
class ForeignKey:
    name: str
    columns: list[str]        # on the owning table, positional
    ref_schema: str
    ref_table: str
    ref_columns: list[str]    # on the referenced table, positional


@dataclass
class Index:
    name: str
    unique: bool
    columns: list[str]


@dataclass
class Table:
    schema: str
    name: str
    kind: str                 # "table" | "view"
    comment: str | None = None
    columns: list[Column] = field(default_factory=list)
    primary_key: list[str] = field(default_factory=list)
    foreign_keys: list[ForeignKey] = field(default_factory=list)
    indexes: list[Index] = field(default_factory=list)

    @property
    def qualified(self) -> str:
        return f"{self.schema}.{self.name}"

    @property
    def key(self) -> str:
        return self.qualified.lower()


@dataclass
class DialectHints:
    """What the agent must know to emit valid SQL for this engine. Data only."""
    dialect: str
    identifier_quote_open: str      # '"' for postgres, '[' for mssql
    identifier_quote_close: str
    default_schema: str             # 'public' / 'dbo'
    row_limit_syntax: str           # 'LIMIT <n>' / 'TOP (<n>)' with placement note
    string_concat: str              # '||' / '+'
    notes: list[str] = field(default_factory=list)


@dataclass
class Catalog:
    dialect: str
    database: str
    hints: DialectHints
    tables: dict[str, Table]        # key = Table.key (lower-cased "schema.table")
    loaded_at: str                  # ISO-8601 UTC
    schemas_filter: list[str] = field(default_factory=list)
