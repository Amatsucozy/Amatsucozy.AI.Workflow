"""Provider contract. One method: load the whole catalog into the normalized model.

Everything above this layer (search, FK graph, tool surface) is dialect-agnostic.
A provider owns exactly three things: connecting, introspecting, and the
DialectHints the agent needs to write syntactically valid SQL for that engine.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from dbschema_mcp.model import Catalog, DialectHints


class SchemaProvider(ABC):
    dialect: str = "unknown"

    def __init__(self, url: str, schemas: list[str] | None = None) -> None:
        self.url = url
        self.schemas = schemas or []  # empty = all non-system schemas

    @abstractmethod
    def hints(self) -> DialectHints: ...

    @abstractmethod
    def load_catalog(self) -> Catalog:
        """Full snapshot. Must be self-contained: open, read, close. Raise on failure."""
